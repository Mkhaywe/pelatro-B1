"""
Enterprise-Grade Gamification Service
Handles missions, badges, leaderboards, and streaks.
"""
import logging
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Max
from django.core.cache import cache

from loyalty.models_khaywe import (
    Mission, MissionProgress, Badge, BadgeAward,
    Leaderboard, LeaderboardEntry, Streak
)
from loyalty.models import LoyaltyAccount
from loyalty.services.points_service import PointsService
from apps.shared.audit import emit_audit_event

logger = logging.getLogger(__name__)


class MissionProgressService:
    """Track and update mission progress"""
    
    def __init__(self):
        self.points_service = PointsService()
    
    def update_progress(
        self,
        mission: Mission,
        customer_id: str,
        progress_data: Dict
    ) -> Dict:
        """
        Update mission progress for a customer.
        
        Returns:
            Dict with progress details
        """
        # Get or create progress
        progress, created = MissionProgress.objects.get_or_create(
            mission=mission,
            customer_id=customer_id,
            defaults={'progress': 0, 'status': 'in_progress'}
        )
        
        # Update progress based on mission type
        if mission.mission_type == 'points_earned':
            points_earned = progress_data.get('points', 0)
            progress.progress = points_earned
        elif mission.mission_type == 'transactions':
            transaction_count = progress_data.get('count', 0)
            progress.progress = transaction_count
        elif mission.mission_type == 'custom':
            # Custom progress tracking
            progress.progress = progress_data.get('progress', progress.progress)
        
        # Check if mission is completed
        if progress.progress >= mission.target_value:
            progress.status = 'completed'
            progress.completed_at = timezone.now()
            
            # Award rewards if any
            if mission.reward_points > 0:
                try:
                    account = LoyaltyAccount.objects.get(
                        customer_id=customer_id,
                        program=mission.program
                    )
                    self.points_service.earn_points(
                        account,
                        mission.reward_points,
                        {
                            'description': f'Mission completed: {mission.name}',
                            'transaction_date': timezone.now()
                        }
                    )
                except LoyaltyAccount.DoesNotExist:
                    logger.warning(f"Account not found for customer {customer_id}")
        
        progress.save()
        
        return {
            'progress_id': str(progress.id),
            'progress': progress.progress,
            'target': mission.target_value,
            'status': progress.status,
            'completed': progress.status == 'completed'
        }


class BadgeAwardService:
    """Award badges to customers"""
    
    def award_badge(
        self,
        badge: Badge,
        customer_id: str,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Award a badge to a customer.
        
        Returns:
            Dict with award details
        """
        # Check if already awarded
        existing = BadgeAward.objects.filter(
            badge=badge,
            customer_id=customer_id
        ).first()
        
        if existing:
            return {
                'success': False,
                'error': 'Badge already awarded',
                'award_id': str(existing.id)
            }
        
        # Create award
        award = BadgeAward.objects.create(
            badge=badge,
            customer_id=customer_id,
            awarded_at=timezone.now(),
            reason=reason or f'Awarded for {badge.name}'
        )
        
        emit_audit_event(
            action='BADGE_AWARDED',
            object_type='BadgeAward',
            object_id=str(award.id),
            details={
                'badge_id': str(badge.id),
                'badge_name': badge.name,
                'customer_id': customer_id
            },
            status='success'
        )
        
        return {
            'success': True,
            'award_id': str(award.id),
            'badge_name': badge.name,
            'awarded_at': award.awarded_at.isoformat()
        }
    
    def check_and_award(
        self,
        badge: Badge,
        customer_id: str,
        context: Dict
    ) -> Dict:
        """
        Check badge criteria and award if met.
        
        Returns:
            Dict with award result
        """
        # Evaluate badge criteria
        if badge.criteria:
            from loyalty.utils import safe_json_logic
            try:
                if not safe_json_logic(badge.criteria, context):
                    return {
                        'success': False,
                        'awarded': False,
                        'reason': 'Criteria not met'
                    }
            except Exception as e:
                logger.error(f"Error evaluating badge criteria: {e}")
                return {
                    'success': False,
                    'error': f'Criteria evaluation error: {str(e)}'
                }
        
        # Award badge
        return self.award_badge(badge, customer_id, 'Criteria met')


class LeaderboardService:
    """Calculate and manage leaderboards"""
    
    def calculate_leaderboard(
        self,
        leaderboard: Leaderboard,
        limit: int = 100
    ) -> List[Dict]:
        """
        Calculate leaderboard rankings.
        
        Returns:
            List of leaderboard entries
        """
        # Get entries ordered by score
        entries = LeaderboardEntry.objects.filter(
            leaderboard=leaderboard,
            is_active=True
        ).order_by('-score', 'updated_at')[:limit]
        
        rankings = []
        rank = 1
        for entry in entries:
            rankings.append({
                'rank': rank,
                'customer_id': str(entry.customer_id),
                'score': entry.score,
                'metadata': entry.metadata or {}
            })
            rank += 1
        
        return rankings
    
    def update_entry(
        self,
        leaderboard: Leaderboard,
        customer_id: str,
        score_delta: float,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Update leaderboard entry for a customer.
        
        Returns:
            Dict with entry details
        """
        entry, created = LeaderboardEntry.objects.get_or_create(
            leaderboard=leaderboard,
            customer_id=customer_id,
            defaults={'score': 0, 'is_active': True}
        )
        
        # Update score
        if leaderboard.scoring_type == 'additive':
            entry.score += score_delta
        elif leaderboard.scoring_type == 'maximum':
            entry.score = max(entry.score, score_delta)
        elif leaderboard.scoring_type == 'latest':
            entry.score = score_delta
        
        if metadata:
            entry.metadata = {**(entry.metadata or {}), **metadata}
        
        entry.updated_at = timezone.now()
        entry.save()
        
        return {
            'entry_id': str(entry.id),
            'customer_id': str(customer_id),
            'score': entry.score,
            'rank': self._get_rank(leaderboard, customer_id)
        }
    
    def _get_rank(
        self,
        leaderboard: Leaderboard,
        customer_id: str
    ) -> int:
        """Get current rank for a customer"""
        try:
            entry = LeaderboardEntry.objects.get(
                leaderboard=leaderboard,
                customer_id=customer_id,
                is_active=True
            )
            # Count entries with higher score
            rank = LeaderboardEntry.objects.filter(
                leaderboard=leaderboard,
                is_active=True,
                score__gt=entry.score
            ).count() + 1
            return rank
        except LeaderboardEntry.DoesNotExist:
            return 0


class StreakService:
    """Track customer streaks"""
    
    def update_streak(
        self,
        streak: Streak,
        customer_id: str,
        action_date: Optional[timezone.datetime] = None
    ) -> Dict:
        """
        Update streak for a customer.
        
        Returns:
            Dict with streak details
        """
        if action_date is None:
            action_date = timezone.now()
        
        # Get or create streak
        customer_streak, created = Streak.objects.get_or_create(
            streak_type=streak.streak_type,
            customer_id=customer_id,
            defaults={
                'current_streak': 0,
                'longest_streak': 0,
                'last_action_date': None
            }
        )
        
        # Check if streak should continue or reset
        if customer_streak.last_action_date:
            days_diff = (action_date.date() - customer_streak.last_action_date.date()).days
            
            if days_diff == 1:
                # Continue streak
                customer_streak.current_streak += 1
            elif days_diff > 1:
                # Reset streak
                customer_streak.current_streak = 1
            # If days_diff == 0, same day - don't update
        else:
            # First action
            customer_streak.current_streak = 1
        
        # Update longest streak
        if customer_streak.current_streak > customer_streak.longest_streak:
            customer_streak.longest_streak = customer_streak.current_streak
        
        customer_streak.last_action_date = action_date
        customer_streak.save()
        
        return {
            'customer_id': str(customer_id),
            'current_streak': customer_streak.current_streak,
            'longest_streak': customer_streak.longest_streak,
            'last_action_date': customer_streak.last_action_date.isoformat()
        }


class GamificationService:
    """
    Main Gamification Service - Orchestrates all gamification operations.
    Enterprise-grade service with missions, badges, leaderboards, and streaks.
    """
    
    def __init__(self):
        self.mission_service = MissionProgressService()
        self.badge_service = BadgeAwardService()
        self.leaderboard_service = LeaderboardService()
        self.streak_service = StreakService()
    
    def update_mission_progress(
        self,
        mission: Mission,
        customer_id: str,
        progress_data: Dict
    ) -> Dict:
        """Update mission progress"""
        return self.mission_service.update_progress(mission, customer_id, progress_data)
    
    def award_badge(
        self,
        badge: Badge,
        customer_id: str,
        reason: Optional[str] = None
    ) -> Dict:
        """Award a badge"""
        return self.badge_service.award_badge(badge, customer_id, reason)
    
    def check_and_award_badge(
        self,
        badge: Badge,
        customer_id: str,
        context: Dict
    ) -> Dict:
        """Check and award badge if criteria met"""
        return self.badge_service.check_and_award(badge, customer_id, context)
    
    def update_leaderboard(
        self,
        leaderboard: Leaderboard,
        customer_id: str,
        score_delta: float,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Update leaderboard entry"""
        return self.leaderboard_service.update_entry(leaderboard, customer_id, score_delta, metadata)
    
    def get_leaderboard(
        self,
        leaderboard: Leaderboard,
        limit: int = 100
    ) -> List[Dict]:
        """Get leaderboard rankings"""
        return self.leaderboard_service.calculate_leaderboard(leaderboard, limit)
    
    def update_streak(
        self,
        streak: Streak,
        customer_id: str,
        action_date: Optional[timezone.datetime] = None
    ) -> Dict:
        """Update streak"""
        return self.streak_service.update_streak(streak, customer_id, action_date)

