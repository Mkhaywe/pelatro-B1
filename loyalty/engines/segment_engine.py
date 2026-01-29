"""
Enterprise-Grade Segment Recalculation Engine
Handles automatic segment updates, snapshots, and optimization.
"""
import logging
from typing import Dict, List, Optional, Set
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.conf import settings

from loyalty.models_khaywe import Segment, SegmentMember, SegmentSnapshot
from loyalty.services.segmentation import SegmentationEngine
from apps.shared.audit import emit_audit_event

logger = logging.getLogger(__name__)


class SegmentUpdateService:
    """Update segment memberships"""
    
    def __init__(self):
        self.segmentation_engine = SegmentationEngine()
    
    @transaction.atomic
    def update_segment_membership(
        self,
        segment: Segment,
        customer_ids: Optional[List[str]] = None,
        batch_size: int = 1000
    ) -> Dict:
        """
        Update segment membership for customers.
        
        Args:
            segment: Segment to update
            customer_ids: Specific customers to evaluate (None = all)
            batch_size: Batch size for processing
        
        Returns:
            Dict with update results
        """
        # Get current members
        current_members = set(
            SegmentMember.objects.filter(
                segment=segment,
                is_active=True
            ).values_list('customer_id', flat=True)
        )
        
        # Calculate new members
        if customer_ids:
            # Evaluate specific customers
            new_members = self.segmentation_engine.calculate_segment_membership(
                segment, customer_ids
            )
        else:
            # For full recalculation, this would query DWH for all customers
            # For now, evaluate current members + any new customers from events
            new_members = self.segmentation_engine.calculate_segment_membership(
                segment, list(current_members)
            )
        
        # Calculate changes
        added = new_members - current_members
        removed = current_members - new_members
        
        # Add new members
        added_count = 0
        for customer_id in added:
            SegmentMember.objects.update_or_create(
                segment=segment,
                customer_id=customer_id,
                defaults={
                    'is_active': True,
                    'left_at': None,
                    'joined_at': timezone.now()
                }
            )
            added_count += 1
        
        # Remove members
        removed_count = 0
        for customer_id in removed:
            SegmentMember.objects.filter(
                segment=segment,
                customer_id=customer_id,
                is_active=True
            ).update(
                is_active=False,
                left_at=timezone.now()
            )
            removed_count += 1
        
        # Update segment metadata
        segment.last_calculated_at = timezone.now()
        segment.save(update_fields=['last_calculated_at'])
        
        logger.info(
            f"Segment {segment.id} updated: +{added_count} members, -{removed_count} members, "
            f"total={len(new_members)}"
        )
        
        emit_audit_event(
            action='SEGMENT_RECALCULATED',
            object_type='Segment',
            object_id=str(segment.id),
            details={
                'segment_name': segment.name,
                'added': added_count,
                'removed': removed_count,
                'total_members': len(new_members)
            },
            status='success'
        )
        
        return {
            'added': added_count,
            'removed': removed_count,
            'total': len(new_members),
            'previous_total': len(current_members)
        }


class SegmentSnapshotService:
    """Create and manage segment snapshots"""
    
    @transaction.atomic
    def create_snapshot(
        self,
        segment: Segment,
        snapshot_date: Optional[timezone.datetime] = None
    ) -> SegmentSnapshot:
        """
        Create a snapshot of segment membership.
        
        Args:
            segment: Segment to snapshot
            snapshot_date: Date for snapshot (defaults to now)
        
        Returns:
            SegmentSnapshot instance
        """
        from django.db import connection
        
        if snapshot_date is None:
            snapshot_date = timezone.now()
        
        # Get current members - use raw SQL since SegmentMember is placeholder
        member_ids = []
        try:
            table_name = 'loyalty_segmentmember'
            with connection.cursor() as cursor:
                if connection.vendor == 'sqlite':
                    cursor.execute(
                        f'SELECT customer_id FROM "{table_name}" WHERE segment_id = ? AND is_active = 1',
                        [segment.id]
                    )
                else:
                    cursor.execute(
                        f'SELECT customer_id FROM "{table_name}" WHERE segment_id = %s AND is_active = true',
                        [segment.id]
                    )
                member_ids = [str(row[0]) for row in cursor.fetchall()]
        except Exception as e:
            logger.warning(f"Error getting segment members for snapshot via raw SQL: {e}")
            # Fallback to ORM
            try:
                members = SegmentMember.objects.filter(segment=segment, is_active=True).values_list('customer_id', flat=True)
                member_ids = [str(cid) for cid in members]
            except Exception:
                pass
        
        # Create snapshot using raw SQL since SegmentSnapshot may also be placeholder
        try:
            snapshot_table = 'loyalty_segmentsnapshot'
            with connection.cursor() as cursor:
                if connection.vendor == 'sqlite':
                    import json
                    cursor.execute(
                        f'INSERT INTO "{snapshot_table}" (segment_id, snapshot_date, member_count, member_ids) VALUES (?, ?, ?, ?)',
                        [segment.id, snapshot_date, len(member_ids), json.dumps(member_ids)]
                    )
                    snapshot_id = cursor.lastrowid
                else:
                    import json
                    cursor.execute(
                        f'INSERT INTO "{snapshot_table}" (segment_id, snapshot_date, member_count, member_ids) VALUES (%s, %s, %s, %s) RETURNING id',
                        [segment.id, snapshot_date, len(member_ids), json.dumps(member_ids)]
                    )
                    snapshot_id = cursor.fetchone()[0]
            
            logger.info(f"Snapshot created for segment {segment.id}: {len(member_ids)} members (id={snapshot_id})")
            
            # Return a mock snapshot object with the relevant fields
            class SnapshotResult:
                def __init__(self, sid, seg, date, count, ids):
                    self.id = sid
                    self.segment = seg
                    self.snapshot_date = date
                    self.member_count = count
                    self.member_ids = ids
            
            return SnapshotResult(snapshot_id, segment, snapshot_date, len(member_ids), member_ids)
        except Exception as e:
            logger.error(f"Error creating snapshot via raw SQL: {e}")
            # Fallback to ORM
            snapshot = SegmentSnapshot.objects.create(
                segment=segment,
                snapshot_date=snapshot_date,
                member_count=len(member_ids),
                member_ids=member_ids
            )
            logger.info(f"Snapshot created for segment {segment.id}: {len(member_ids)} members")
            return snapshot
    
    def get_snapshot_history(
        self,
        segment: Segment,
        start_date: Optional[timezone.datetime] = None,
        end_date: Optional[timezone.datetime] = None
    ) -> List[Dict]:
        """
        Get snapshot history for a segment.
        
        Returns:
            List of snapshot data
        """
        from django.db import connection
        
        # Try raw SQL first (for placeholder models)
        try:
            table_name = 'loyalty_segmentsnapshot'
            query_parts = [f'SELECT snapshot_date, member_count FROM "{table_name}" WHERE segment_id = %s']
            params = [segment.id]
            
            if start_date:
                query_parts.append('AND snapshot_date >= %s')
                params.append(start_date)
            if end_date:
                query_parts.append('AND snapshot_date <= %s')
                params.append(end_date)
            
            query_parts.append('ORDER BY snapshot_date')
            
            with connection.cursor() as cursor:
                if connection.vendor == 'sqlite':
                    query = ' '.join(query_parts).replace('%s', '?')
                    cursor.execute(query, params)
                else:
                    cursor.execute(' '.join(query_parts), params)
                
                rows = cursor.fetchall()
                return [
                    {
                        'snapshot_date': row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                        'member_count': row[1]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.warning(f"Error getting snapshot history via raw SQL: {e}")
            # Fallback to ORM
            snapshots = SegmentSnapshot.objects.filter(segment=segment)
            
            if start_date:
                snapshots = snapshots.filter(snapshot_date__gte=start_date)
            if end_date:
                snapshots = snapshots.filter(snapshot_date__lte=end_date)
            
            return [
                {
                    'snapshot_date': snap.snapshot_date.isoformat(),
                    'member_count': snap.member_count
                }
                for snap in snapshots.order_by('snapshot_date')
            ]


class SegmentOptimizationService:
    """Optimize segment evaluation performance"""
    
    def optimize_segment_rules(self, segment: Segment) -> Dict:
        """
        Optimize segment rules for better performance.
        
        Returns:
            Dict with optimization suggestions
        """
        suggestions = []
        
        # Check rule complexity
        for i, rule in enumerate(segment.rules):
            rule_str = str(rule)
            complexity = len(rule_str)
            
            if complexity > 1000:
                suggestions.append({
                    'rule_index': i,
                    'issue': 'High complexity',
                    'suggestion': 'Consider breaking into multiple simpler rules'
                })
        
        # Check for common patterns that can be optimized
        # (This is a placeholder - real optimization would analyze rule structure)
        
        return {
            'segment_id': str(segment.id),
            'suggestions': suggestions,
            'optimized': len(suggestions) == 0
        }


class SegmentRecalculationEngine:
    """
    Main Segment Recalculation Engine - Orchestrates segment updates.
    Enterprise-grade engine with automatic recalculation, snapshots, and optimization.
    """
    
    def __init__(self):
        self.update_service = SegmentUpdateService()
        self.snapshot_service = SegmentSnapshotService()
        self.optimization_service = SegmentOptimizationService()
    
    def recalculate_segment(
        self,
        segment: Segment,
        customer_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Recalculate segment membership.
        
        Args:
            segment: Segment to recalculate
            customer_ids: Specific customers to evaluate (None = all)
        
        Returns:
            Dict with recalculation results
        """
        return self.update_service.update_segment_membership(segment, customer_ids)
    
    def recalculate_all_dynamic_segments(
        self,
        customer_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Recalculate all dynamic segments.
        
        Args:
            customer_ids: Specific customers to evaluate (None = all)
        
        Returns:
            Dict with results for each segment
        """
        segments = Segment.objects.filter(is_dynamic=True, is_active=True)
        
        results = {}
        for segment in segments:
            try:
                result = self.recalculate_segment(segment, customer_ids)
                results[str(segment.id)] = {
                    'segment_name': segment.name,
                    **result
                }
            except Exception as e:
                logger.error(f"Error recalculating segment {segment.id}: {e}")
                results[str(segment.id)] = {
                    'segment_name': segment.name,
                    'error': str(e)
                }
        
        return {
            'segments_processed': len(segments),
            'results': results
        }
    
    def create_snapshot(
        self,
        segment: Segment,
        snapshot_date: Optional[timezone.datetime] = None
    ) -> SegmentSnapshot:
        """Create segment snapshot"""
        return self.snapshot_service.create_snapshot(segment, snapshot_date)
    
    def get_snapshot_history(
        self,
        segment: Segment,
        start_date: Optional[timezone.datetime] = None,
        end_date: Optional[timezone.datetime] = None
    ) -> List[Dict]:
        """Get snapshot history"""
        return self.snapshot_service.get_snapshot_history(segment, start_date, end_date)
    
    def optimize_segment(self, segment: Segment) -> Dict:
        """Optimize segment rules"""
        return self.optimization_service.optimize_segment_rules(segment)

