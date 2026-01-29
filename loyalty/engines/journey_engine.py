"""
Enterprise-Grade Journey Execution Engine
Handles journey state machine, routing, actions, and analytics.
"""
import logging
from typing import Dict, List, Optional, Set
from enum import Enum
from datetime import datetime
from django.utils import timezone
from django.db import transaction

from loyalty.models_khaywe import Journey, JourneyNode, JourneyEdge, JourneyExecution
from loyalty.services.segmentation import SegmentationEngine
from apps.shared.audit import emit_audit_event

logger = logging.getLogger(__name__)


class JourneyNodeType(Enum):
    """Journey node types"""
    START = 'start'
    CONDITION = 'condition'
    ACTION = 'action'
    WAIT = 'wait'
    END = 'end'


class JourneyState(Enum):
    """Journey execution states"""
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    WAITING = 'waiting'
    COMPLETED = 'completed'
    FAILED = 'failed'
    ABANDONED = 'abandoned'


class JourneyStateMachine:
    """Manage journey execution state"""
    
    def __init__(self, journey: Journey):
        self.journey = journey
        self.nodes = {node.id: node for node in journey.nodes.all()}
        self.edges = list(journey.edges.all())
    
    def get_start_node(self) -> Optional[JourneyNode]:
        """Get the start node of the journey"""
        for node in self.nodes.values():
            if node.node_type == JourneyNodeType.START.value:
                return node
        return None
    
    def get_next_nodes(
        self,
        current_node_id: str,
        context: Dict
    ) -> List[JourneyNode]:
        """
        Get next nodes based on current node and context.
        
        Args:
            current_node_id: Current node ID (string or int)
            context: Execution context
        
        Returns:
            List of next nodes
        """
        next_nodes = []
        
        # Find edges from current node
        for edge in self.edges:
            # Compare node IDs (handle both string and int)
            from_node_id = str(edge.from_node.id) if edge.from_node else None
            if from_node_id == str(current_node_id):
                # Check edge condition if any
                if edge.condition:
                    from loyalty.utils import safe_json_logic
                    try:
                        if not safe_json_logic(edge.condition, context):
                            continue
                    except Exception as e:
                        logger.error(f"Error evaluating edge condition: {e}")
                        continue
                
                # Get target node
                target_node = self.nodes.get(edge.to_node_id)
                if target_node:
                    next_nodes.append(target_node)
        
        return next_nodes
    
    def execute_node(
        self,
        node: JourneyNode,
        context: Dict
    ) -> Dict:
        """
        Execute a journey node.
        
        Args:
            node: Node to execute
            context: Execution context
        
        Returns:
            Dict with execution result
        """
        if node.node_type == JourneyNodeType.START.value:
            return {'success': True, 'action': 'start', 'next_state': JourneyState.IN_PROGRESS.value}
        
        elif node.node_type == JourneyNodeType.CONDITION.value:
            # Evaluate condition
            if node.config and 'condition' in node.config:
                from loyalty.utils import safe_json_logic
                try:
                    condition_result = safe_json_logic(node.config['condition'], context)
                    return {
                        'success': True,
                        'action': 'condition',
                        'condition_result': condition_result,
                        'next_state': JourneyState.IN_PROGRESS.value
                    }
                except Exception as e:
                    logger.error(f"Error evaluating condition: {e}")
                    return {'success': False, 'error': str(e)}
            return {'success': True, 'action': 'condition', 'next_state': JourneyState.IN_PROGRESS.value}
        
        elif node.node_type == JourneyNodeType.ACTION.value:
            # Execute action using action executor
            from loyalty.services.journey_actions import JourneyActionExecutor
            
            action_type = node.config.get('action_type') if node.config else None
            if not action_type:
                return {
                    'success': False,
                    'error': 'action_type not specified in node config'
                }
            
            executor = JourneyActionExecutor()
            action_result = executor.execute_action(
                action_type=action_type,
                config=node.config or {},
                context=context
            )
            
            if not action_result.get('success'):
                logger.error(f"Action execution failed: {action_result.get('error')}")
                return {
                    'success': False,
                    'error': action_result.get('error', 'Action execution failed'),
                    'action_type': action_type
                }
            
            # Store action result in context for later nodes
            context[f'action_result_{node.id}'] = action_result
            
            return {
                'success': True,
                'action': 'action',
                'action_type': action_type,
                'action_result': action_result,
                'next_state': JourneyState.IN_PROGRESS.value
            }
        
        elif node.node_type == JourneyNodeType.WAIT.value:
            # Wait for event or time
            wait_type = node.config.get('wait_type') if node.config else None
            return {
                'success': True,
                'action': 'wait',
                'wait_type': wait_type,
                'next_state': JourneyState.WAITING.value
            }
        
        elif node.node_type == JourneyNodeType.END.value:
            return {
                'success': True,
                'action': 'end',
                'next_state': JourneyState.COMPLETED.value
            }
        
        return {'success': False, 'error': f'Unknown node type: {node.node_type}'}


class JourneyExecutionService:
    """Execute journeys for customers"""
    
    def __init__(self):
        self.segmentation_engine = SegmentationEngine()
    
    def start_journey(
        self,
        journey: Journey,
        customer_id: str,
        context: Optional[Dict] = None
    ) -> JourneyExecution:
        """
        Start a journey for a customer.
        
        Args:
            journey: Journey to start
            customer_id: Customer to start journey for
            context: Initial context
        
        Returns:
            JourneyExecution instance
        """
        if context is None:
            context = {}
        
        context['customer_id'] = customer_id
        context['journey_id'] = str(journey.id)
        
        # Create execution
        execution = JourneyExecution.objects.create(
            journey=journey,
            customer_id=customer_id,
            state=JourneyState.NOT_STARTED.value,
            status='active',  # Map state to status
            current_node=None,
            context=context
        )
        
        # Get start node
        state_machine = JourneyStateMachine(journey)
        start_node = state_machine.get_start_node()
        
        if not start_node:
            execution.state = JourneyState.FAILED.value
            execution.status = 'abandoned'
            execution.save()
            return execution
        
        # Execute start node
        execution.current_node = start_node
        execution.state = JourneyState.IN_PROGRESS.value
        execution.status = 'active'
        execution.save()
        
        # Continue execution
        self.continue_journey(execution)
        
        return execution
    
    def continue_journey(
        self,
        execution: JourneyExecution,
        event_data: Optional[Dict] = None
    ) -> Dict:
        """
        Continue journey execution from current node.
        
        Args:
            execution: JourneyExecution to continue
            event_data: Event data if waiting for event
        
        Returns:
            Dict with execution result
        """
        if execution.state == JourneyState.COMPLETED.value:
            return {'success': True, 'state': 'completed', 'message': 'Journey already completed'}
        
        if execution.state == JourneyState.FAILED.value:
            return {'success': False, 'state': 'failed', 'message': 'Journey has failed'}
        
        journey = execution.journey
        state_machine = JourneyStateMachine(journey)
        
        # Get current node
        if execution.current_node:
            current_node = execution.current_node
            # Also get from state machine to ensure it's in the journey
            current_node = state_machine.nodes.get(str(current_node.id), current_node)
        else:
            return {'success': False, 'error': 'No current node'}
        
        if not current_node:
            execution.state = JourneyState.FAILED.value
            execution.status = 'abandoned'
            execution.save()
            return {'success': False, 'error': 'Current node not found'}
        
        # Merge event data into context
        context = execution.context or {}
        if event_data:
            context.update(event_data)
        
        # Execute current node
        node_result = state_machine.execute_node(current_node, context)
        
        if not node_result.get('success'):
            execution.state = JourneyState.FAILED.value
            execution.status = 'abandoned'
            execution.context = context
            execution.save()
            return node_result
        
        # Update execution context
        execution.context = context
        
        # Handle next state
        next_state = node_result.get('next_state')
        if next_state == JourneyState.WAITING.value:
            execution.state = JourneyState.WAITING.value
            execution.save()
            return {
                'success': True,
                'state': 'waiting',
                'current_node': current_node.name,
                'wait_type': node_result.get('wait_type')
            }
        
        elif next_state == JourneyState.COMPLETED.value:
            execution.state = JourneyState.COMPLETED.value
            execution.status = 'completed'
            execution.completed_at = timezone.now()
            execution.save()
            
            emit_audit_event(
                action='JOURNEY_COMPLETED',
                object_type='JourneyExecution',
                object_id=str(execution.id),
                details={
                    'journey_id': str(journey.id),
                    'journey_name': journey.name,
                    'customer_id': str(execution.customer_id)
                },
                status='success'
            )
            
            return {
                'success': True,
                'state': 'completed',
                'message': 'Journey completed'
            }
        
        # Get next nodes
        next_nodes = state_machine.get_next_nodes(str(current_node.id), context)
        
        if not next_nodes:
            # No next nodes = journey ends
            execution.state = JourneyState.COMPLETED.value
            execution.status = 'completed'
            execution.completed_at = timezone.now()
            execution.save()
            return {
                'success': True,
                'state': 'completed',
                'message': 'Journey completed (no more nodes)'
            }
        
        # Move to first next node (in real implementation, handle multiple paths)
        next_node = next_nodes[0]
        execution.current_node = next_node
        execution.state = JourneyState.IN_PROGRESS.value
        execution.status = 'active'
        execution.save()
        
        # Recursively continue if not waiting
        if next_node.node_type != JourneyNodeType.WAIT.value:
            return self.continue_journey(execution)
        
        return {
            'success': True,
            'state': 'in_progress',
            'current_node': next_node.name
        }
    
    def process_journey_event(
        self,
        customer_id: str,
        event_type: str,
        event_data: Dict
    ) -> List[Dict]:
        """
        Process an event for journeys waiting on that event.
        
        Args:
            customer_id: Customer ID
            event_type: Type of event
            event_data: Event data
        
        Returns:
            List of execution results
        """
        # Find journeys waiting for this event
        executions = JourneyExecution.objects.filter(
            customer_id=customer_id,
            state=JourneyState.WAITING.value
        )
        
        results = []
        
        for execution in executions:
            journey = execution.journey
            state_machine = JourneyStateMachine(journey)
            
            # Get current node
            if not execution.current_node:
                continue
            
            current_node = execution.current_node
            # Verify it's in the journey's nodes
            if str(current_node.id) not in state_machine.nodes:
                continue
            if not current_node or current_node.node_type != JourneyNodeType.WAIT.value:
                continue
            
            # Check if waiting for this event
            wait_config = current_node.config or {}
            wait_event = wait_config.get('wait_event')
            
            if wait_event == event_type:
                # Continue journey
                result = self.continue_journey(execution, event_data)
                results.append({
                    'journey_id': str(journey.id),
                    'execution_id': str(execution.id),
                    **result
                })
        
        return results


class JourneyAnalyticsService:
    """Track and analyze journey performance"""
    
    def get_journey_analytics(
        self,
        journey: Journey,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get journey analytics.
        
        Returns:
            Dict with analytics
        """
        executions = JourneyExecution.objects.filter(journey=journey)
        
        if start_date:
            executions = executions.filter(created_at__gte=start_date)
        if end_date:
            executions = executions.filter(created_at__lte=end_date)
        
        total_started = executions.count()
        total_completed = executions.filter(state=JourneyState.COMPLETED.value).count()
        total_failed = executions.filter(state=JourneyState.FAILED.value).count()
        total_abandoned = executions.filter(state=JourneyState.ABANDONED.value).count()
        in_progress = executions.filter(state=JourneyState.IN_PROGRESS.value).count()
        waiting = executions.filter(state=JourneyState.WAITING.value).count()
        
        # Calculate average completion time
        completed_executions = executions.filter(
            state=JourneyState.COMPLETED.value,
            completed_at__isnull=False
        )
        
        avg_completion_time = None
        if completed_executions.exists():
            total_time = sum(
                (ex.completed_at - ex.created_at).total_seconds()
                for ex in completed_executions
            )
            avg_completion_time = total_time / completed_executions.count()
        
        return {
            'journey_id': str(journey.id),
            'journey_name': journey.name,
            'total_started': total_started,
            'total_completed': total_completed,
            'total_failed': total_failed,
            'total_abandoned': total_abandoned,
            'in_progress': in_progress,
            'waiting': waiting,
            'completion_rate': (total_completed / total_started * 100) if total_started > 0 else 0,
            'failure_rate': (total_failed / total_started * 100) if total_started > 0 else 0,
            'avg_completion_time_seconds': avg_completion_time
        }


class JourneyExecutionEngine:
    """
    Main Journey Execution Engine - Orchestrates journey execution.
    Enterprise-grade engine with state machine, event handling, and analytics.
    """
    
    def __init__(self):
        self.execution_service = JourneyExecutionService()
        self.analytics_service = JourneyAnalyticsService()
    
    def start_journey(
        self,
        journey: Journey,
        customer_id: str,
        context: Optional[Dict] = None
    ) -> JourneyExecution:
        """Start a journey for a customer"""
        return self.execution_service.start_journey(journey, customer_id, context)
    
    def continue_journey(
        self,
        execution: JourneyExecution,
        event_data: Optional[Dict] = None
    ) -> Dict:
        """Continue journey execution"""
        return self.execution_service.continue_journey(execution, event_data)
    
    def process_event(
        self,
        customer_id: str,
        event_type: str,
        event_data: Dict
    ) -> List[Dict]:
        """Process event for journeys"""
        return self.execution_service.process_journey_event(customer_id, event_type, event_data)
    
    def get_analytics(
        self,
        journey: Journey,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get journey analytics"""
        return self.analytics_service.get_journey_analytics(journey, start_date, end_date)

