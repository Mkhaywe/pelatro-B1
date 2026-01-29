"""
Segmentation Engine that queries DWH for customer attributes.
"""

from typing import List, Set
from loyalty.models_khaywe import Segment, SegmentMember
from loyalty.integration.feature_store import FeatureStore
from loyalty.utils import safe_json_logic
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class SegmentationEngine:
    """Segmentation engine with DWH integration"""
    
    @staticmethod
    def _get_segment_rules_from_db(segment_id: int):
        """
        Load segment rules directly from the real DB table (loyalty_segment).
        We CANNOT rely on segment.rules because Segment is a placeholder model.
        """
        from django.db import connection
        import json

        table_name = 'loyalty_segment'
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f'SELECT rules FROM "{table_name}" WHERE id = %s',
                    [segment_id],
                )
                row = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error reading rules for segment {segment_id} from {table_name}: {e}", exc_info=True)
            return []

        if not row:
            return []

        rules_val = row[0]
        if rules_val is None or rules_val == '' or rules_val == '[]':
            return []

        # If stored as JSON string, parse it
        if isinstance(rules_val, str):
            try:
                rules_val = json.loads(rules_val)
            except Exception as e:
                logger.warning(f"Failed to parse rules JSON for segment {segment_id}: {e}")
                return []

        # Ensure list
        if isinstance(rules_val, dict):
            rules_val = [rules_val]
        if not isinstance(rules_val, list):
            return []

        return rules_val

    @staticmethod
    def evaluate_segment(segment: Segment, customer_id: str) -> bool:
        """Evaluate if customer matches segment rules"""
        # NOTE: Segment is a placeholder model that does NOT have a 'rules' field.
        # We must load rules directly from the DB, not via segment.rules.
        rules = SegmentationEngine._get_segment_rules_from_db(segment.id)
        if not rules:
            logger.warning(f"No rules defined for segment {segment.id}; customer {customer_id} will not match")
            return False

        # Get customer features from DWH
        features = FeatureStore.get_customer_features(customer_id)
        
        if not features:
            logger.warning(f"No features found for customer {customer_id}")
            return False
        
        # Evaluate each rule
        for rule_item in rules:
            try:
                # Handle new format: {name: "...", rule: {...}}
                if isinstance(rule_item, dict) and 'rule' in rule_item:
                    rule_logic = rule_item['rule']
                # Handle old format: just JSONLogic object
                else:
                    rule_logic = rule_item
                
                if not safe_json_logic(rule_logic, features):
                    return False
            except Exception as e:
                logger.error(f"Rule evaluation error for segment {segment.id}: {e}")
                return False
        
        return True
    
    @staticmethod
    def calculate_segment_membership(segment: Segment, customer_ids: List[str] = None) -> Set[str]:
        """Calculate segment membership for customers"""
        members = set()
        
        # If customer_ids provided, evaluate only those
        if customer_ids:
            for customer_id in customer_ids:
                if SegmentationEngine.evaluate_segment(segment, customer_id):
                    members.add(customer_id)
        else:
            # For dynamic segments, get all customers from DWH or Xiva
            # Try to get customers from DWH first
            try:
                from loyalty.integration.dwh import get_dwh_connector
                from django.conf import settings
                connector = get_dwh_connector()
                
                # Get table name from settings
                table_name = getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view')
                
                # Query DWH for all customer IDs
                # Use parameterized query format based on DWH type
                query = f"SELECT DISTINCT customer_id FROM {table_name}"
                results = connector.execute_query(query)
                customer_ids = [str(row['customer_id']) for row in results if row.get('customer_id')]
                
                logger.info(f"Found {len(customer_ids)} customers in DWH for segment calculation")
            except Exception as e:
                logger.warning(f"Could not get customers from DWH: {e}")
                # Fallback: Try to get from Xiva
                try:
                    from loyalty.integration.xiva_client import get_xiva_client
                    client = get_xiva_client()
                    customers = client.get_customer_list(limit=1000)
                    customer_ids = [str(c.get('id', c.get('customer_id', ''))) for c in customers if c.get('id') or c.get('customer_id')]
                    logger.info(f"Found {len(customer_ids)} customers from Xiva for segment calculation")
                except Exception as e2:
                    logger.error(f"Could not get customers from Xiva: {e2}")
                    logger.warning("No customer list available - segment calculation may be incomplete")
                    customer_ids = []
            
            # Evaluate segment for each customer
            total = len(customer_ids)
            for idx, customer_id in enumerate(customer_ids):
                if idx % 100 == 0:
                    logger.info(f"Evaluating segment {segment.id}: {idx}/{total} customers processed")
                
                try:
                    if SegmentationEngine.evaluate_segment(segment, customer_id):
                        members.add(customer_id)
                except Exception as e:
                    logger.warning(f"Error evaluating customer {customer_id} for segment {segment.id}: {e}")
                    continue
        
        return members
    
    @staticmethod
    def update_segment_membership(segment: Segment, customer_ids: List[str] = None):
        """Update segment membership (called periodically or on-demand)"""
        from django.db import connection

        # ------------------------------------------------------------------
        # 1) Get current members
        # ------------------------------------------------------------------
        placeholder_model = hasattr(SegmentMember._meta, 'managed') and SegmentMember._meta.managed is False

        if placeholder_model:
            # Use raw SQL against the real table (loyalty_segmentmember)
            table_name = 'loyalty_segmentmember'
            current_members: set[str] = set()
            try:
                with connection.cursor() as cursor:
                    # Discover column names to be safe
                    if connection.vendor == 'sqlite':
                        cursor.execute(f"PRAGMA table_info('{table_name}')")
                        cols_info = cursor.fetchall()
                        col_names = [c[1] for c in cols_info]
                    else:
                        cursor.execute(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = %s",
                            [table_name],
                        )
                        col_names = [c[0] for c in cursor.fetchall()]

                    if 'customer_id' not in col_names:
                        logger.warning(
                            f"{table_name} does not have customer_id column; cannot update membership"
                        )
                        return {
                            'success': False,
                            'error': 'SegmentMember table missing customer_id column',
                            'added': 0,
                            'removed': 0,
                        }

                    seg_col = 'segment_id' if 'segment_id' in col_names else 'segment'
                    active_filter = 'is_active = 1' if 'is_active' in col_names and connection.vendor == 'sqlite' else 'is_active = true'

                    cursor.execute(
                        f'SELECT customer_id FROM "{table_name}" '
                        f'WHERE {seg_col} = %s AND {active_filter}',
                        [segment.id],
                    )
                    rows = cursor.fetchall()
                    for (cust_id,) in rows:
                        current_members.add(str(cust_id))
            except Exception as e:
                logger.warning(f"Error reading current segment members via raw SQL: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': f'Failed to read current members: {str(e)}',
                    'added': 0,
                    'removed': 0,
                }
        else:
            # Normal ORM path
            try:
                current_members = set(
                    SegmentMember.objects.filter(
                        segment=segment,
                        is_active=True,
                    ).values_list('customer_id', flat=True)
                )
            except Exception as e:
                logger.warning(
                    "SegmentMember model doesn't have required fields (likely placeholder): %s", e
                )
                return {
                    'success': False,
                    'error': f'SegmentMember model not fully migrated: {str(e)}',
                    'added': 0,
                    'removed': 0,
                }
        
        # Calculate new members from DWH
        new_members = SegmentationEngine.calculate_segment_membership(segment, customer_ids)
        
        # ------------------------------------------------------------------
        # 2) Add / remove members
        # ------------------------------------------------------------------
        added_count = 0
        removed_count = 0

        if placeholder_model:
            table_name = 'loyalty_segmentmember'
            try:
                with connection.cursor() as cursor:
                    # Detect column names again for safety
                    if connection.vendor == 'sqlite':
                        cursor.execute(f"PRAGMA table_info('{table_name}')")
                        cols_info = cursor.fetchall()
                        col_names = [c[1] for c in cols_info]
                    else:
                        cursor.execute(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = %s",
                            [table_name],
                        )
                        col_names = [c[0] for c in cursor.fetchall()]

                    seg_col = 'segment_id' if 'segment_id' in col_names else 'segment'

                    # Add new members
                    for customer_id in new_members - current_members:
                        try:
                            # Upsert style: try UPDATE first
                            if connection.vendor == 'sqlite':
                                cursor.execute(
                                    f'UPDATE "{table_name}" '
                                    f'SET is_active = 1, left_at = NULL '
                                    f'WHERE {seg_col} = ? AND customer_id = ?',
                                    [segment.id, customer_id],
                                )
                            else:
                                cursor.execute(
                                    f'UPDATE "{table_name}" '
                                    f'SET is_active = true, left_at = NULL '
                                    f'WHERE {seg_col} = %s AND customer_id = %s',
                                    [segment.id, customer_id],
                                )

                            if cursor.rowcount == 0:
                                # No existing row, INSERT
                                if connection.vendor == 'sqlite':
                                    cursor.execute(
                                        f'INSERT INTO "{table_name}" '
                                        f'({seg_col}, customer_id, joined_at, is_active) '
                                        f'VALUES (?, ?, CURRENT_TIMESTAMP, 1)',
                                        [segment.id, customer_id],
                                    )
                                else:
                                    cursor.execute(
                                        f'INSERT INTO "{table_name}" '
                                        f'({seg_col}, customer_id, joined_at, is_active) '
                                        f"VALUES (%s, %s, NOW(), true)",
                                        [segment.id, customer_id],
                                    )
                            added_count += 1
                        except Exception as e:
                            logger.warning(
                                "Error adding member %s to segment %s via raw SQL: %s",
                                customer_id,
                                segment.id,
                                e,
                            )
                            continue

                    # Deactivate removed members
                    for customer_id in current_members - new_members:
                        try:
                            if connection.vendor == 'sqlite':
                                cursor.execute(
                                    f'UPDATE "{table_name}" '
                                    f'SET is_active = 0, left_at = CURRENT_TIMESTAMP '
                                    f'WHERE {seg_col} = ? AND customer_id = ?',
                                    [segment.id, customer_id],
                                )
                            else:
                                cursor.execute(
                                    f'UPDATE "{table_name}" '
                                    f'SET is_active = false, left_at = NOW() '
                                    f'WHERE {seg_col} = %s AND customer_id = %s',
                                    [segment.id, customer_id],
                                )
                            if cursor.rowcount > 0:
                                removed_count += 1
                        except Exception as e:
                            logger.warning(
                                "Error deactivating member %s from segment %s via raw SQL: %s",
                                customer_id,
                                segment.id,
                                e,
                            )
                            continue
            except Exception as e:
                logger.warning(f"Error updating segment members via raw SQL: {e}", exc_info=True)
        else:
            # Normal ORM path
            for customer_id in new_members - current_members:
                try:
                    SegmentMember.objects.update_or_create(
                        segment=segment,
                        customer_id=customer_id,
                        defaults={
                            'is_active': True,
                            'left_at': None,
                        },
                    )
                    added_count += 1
                except Exception as e:
                    logger.warning(
                        "Error adding member %s to segment %s: %s",
                        customer_id,
                        segment.id,
                        e,
                    )
                    continue

            for customer_id in current_members - new_members:
                try:
                    SegmentMember.objects.filter(
                        segment=segment,
                        customer_id=customer_id,
                    ).update(is_active=False, left_at=timezone.now())
                    removed_count += 1
                except Exception as e:
                    logger.warning(
                        "Error removing member %s from segment %s: %s",
                        customer_id,
                        segment.id,
                        e,
                    )
                    continue
        
        logger.info(
            f"Segment {segment.id} updated: +{added_count} members, -{removed_count} members"
        )
        
        # Create snapshot after update (for historical tracking)
        try:
            from loyalty.engines.segment_engine import SegmentSnapshotService
            snapshot_service = SegmentSnapshotService()
            snapshot_service.create_snapshot(segment)
        except Exception as e:
            logger.warning(f"Failed to create snapshot for segment {segment.id}: {e}")
        
        # Update last_calculated_at
        try:
            # Segment is a placeholder model; update the real table directly
            from django.db import connection
            table_name = 'loyalty_segment'
            with connection.cursor() as cursor:
                if connection.vendor == 'sqlite':
                    cursor.execute(
                        f'UPDATE "{table_name}" SET last_calculated_at = CURRENT_TIMESTAMP WHERE id = ?',
                        [segment.id],
                    )
                else:
                    cursor.execute(
                        f'UPDATE "{table_name}" SET last_calculated_at = NOW() WHERE id = %s',
                        [segment.id],
                    )
        except Exception as e:
            # Don't fail the whole operation if this auxiliary update fails
            logger.warning(
                f"Failed to update last_calculated_at for segment {segment.id}: {e}"
            )
        
        return {
            'added': added_count,
            'removed': removed_count,
            'total': len(new_members)
        }

