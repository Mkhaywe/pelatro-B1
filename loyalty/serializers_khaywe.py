"""
Serializers for Khaywe models.
"""

from rest_framework import serializers
from loyalty.models_khaywe import (
    Campaign, CampaignExecution,
    Segment, SegmentMember, SegmentSnapshot,
    Mission, MissionProgress, Badge, BadgeAward, Leaderboard, LeaderboardEntry, Streak,
    Journey, JourneyNode, JourneyEdge, JourneyExecution,
    Experiment, ExperimentAssignment, HoldoutGroup,
    Partner, PartnerProgram, PartnerSettlement, Coalition,
    Role, Permission, RolePermission, UserRole,
    ApprovalWorkflow, ApprovalRequest, ApprovalDecision,
    PointsExpiryRule, PointsExpiryEvent,
    EarnCap, CapUsage,
    DataSourceConfig, CustomerEvent, CustomerBehaviorScore, MissionTemplate,
)


def get_field_from_db(obj, field_name, default=None, table_name=None):
    """Helper function to get field value from database for placeholder models"""
    try:
        # First try to get attribute directly (works if model has field)
        if hasattr(obj, field_name):
            value = getattr(obj, field_name)
            if value is not None:
                return value
    except (AttributeError, Exception):
        pass
    
    # If model is placeholder, query database directly
    try:
        if hasattr(obj, '_meta') and hasattr(obj._meta, 'managed') and obj._meta.managed == False:
            from django.db import connection
            
            # Get model name first (needed for segment check)
            model_name = obj.__class__.__name__.lower()
            
            # Determine table name
            if table_name:
                db_table = table_name
            elif hasattr(obj._meta, 'db_table') and obj._meta.db_table:
                db_table = obj._meta.db_table
            else:
                # Django convention: app_label_modelname -> loyalty_campaign, loyalty_segment, etc.
                app_label = obj._meta.app_label if hasattr(obj._meta, 'app_label') else 'loyalty'
                db_table = f"{app_label}_{model_name}"
            
            # For Segment model, check actual table name in database
            if model_name == 'segment':
                # Check if table exists with different name
                with connection.cursor() as check_cursor:
                    if connection.vendor == 'sqlite':
                        check_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='segment' OR name='loyalty_segment')")
                    else:
                        check_cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name IN ('segment', 'loyalty_segment')")
                    result = check_cursor.fetchone()
                    if result:
                        db_table = result[0]
            
            with connection.cursor() as cursor:
                # Use parameterized query based on database backend
                if connection.vendor == 'sqlite':
                    cursor.execute(f'SELECT "{field_name}" FROM "{db_table}" WHERE id = ?', [obj.id])
                else:
                    cursor.execute(f'SELECT "{field_name}" FROM "{db_table}" WHERE id = %s', [obj.id])
                row = cursor.fetchone()
                if row and row[0] is not None:
                    value = row[0]
                    # Handle JSON fields stored as text in SQLite
                    if isinstance(value, str) and field_name in ['rules', 'rfm_config', 'eligibility_rules']:
                        import json
                        try:
                            return json.loads(value)
                        except (json.JSONDecodeError, ValueError):
                            return value
                    return value
    except Exception as e:
        # Silently fail - return default
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Could not get field {field_name} from database for {obj.__class__.__name__}: {e}")
        pass
    
    return default


def save_fields_to_db(obj, fields_dict, table_name=None):
    """
    Generic helper to save fields directly to database for placeholder models.
    
    Args:
        obj: Model instance with an id
        fields_dict: Dict of field_name -> value to save
        table_name: Override table name (otherwise inferred from model)
    
    Returns:
        True if successful, False otherwise
    """
    import json
    import logging
    from django.db import connection
    
    logger = logging.getLogger(__name__)
    
    if not fields_dict:
        return True
    
    try:
        # Determine table name
        if not table_name:
            if hasattr(obj._meta, 'db_table') and obj._meta.db_table:
                table_name = obj._meta.db_table
            else:
                model_name = obj.__class__.__name__.lower()
                app_label = getattr(obj._meta, 'app_label', 'loyalty')
                table_name = f"{app_label}_{model_name}"
        
        # Get existing columns in the table to avoid updating non-existent columns
        with connection.cursor() as cursor:
            if connection.vendor == 'sqlite':
                cursor.execute(f"PRAGMA table_info('{table_name}')")
                existing_columns = {col[1] for col in cursor.fetchall()}
            else:
                cursor.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
                    [table_name]
                )
                existing_columns = {col[0] for col in cursor.fetchall()}
        
        # Build SET clause, only including columns that exist
        set_parts = []
        values = []
        
        for field_name, value in fields_dict.items():
            if value is None:
                continue
            
            # Skip fields that don't exist in the table
            if field_name not in existing_columns:
                logger.debug(f"Skipping field '{field_name}' - not in table {table_name}")
                continue
            
            set_parts.append(f'"{field_name}" = %s')
            
            # Handle special types
            if isinstance(value, (dict, list)):
                values.append(json.dumps(value))
            elif isinstance(value, bool):
                if connection.vendor == 'sqlite':
                    values.append(1 if value else 0)
                else:
                    values.append(value)
            else:
                values.append(value)
        
        if not set_parts:
            logger.debug(f"No valid fields to update for {table_name} id={obj.id}")
            return True
        
        # Add object id for WHERE clause
        values.append(obj.id)
        
        # Execute UPDATE
        set_clause = ', '.join(set_parts)
        
        with connection.cursor() as cursor:
            if connection.vendor == 'sqlite':
                # SQLite uses ? placeholders
                query = f'UPDATE "{table_name}" SET {set_clause.replace("%s", "?")} WHERE id = ?'
            else:
                query = f'UPDATE "{table_name}" SET {set_clause} WHERE id = %s'
            
            cursor.execute(query, values)
            logger.info(f"Updated {table_name} id={obj.id} with fields: {[f for f in fields_dict.keys() if f in existing_columns]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving fields to {table_name} for id={obj.id}: {e}", exc_info=True)
        return False


# ============================================================================
# CAMPAIGN MANAGEMENT
# ============================================================================

class CampaignSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = '__all__'
    
    def get_name(self, obj):
        """Get name field, handling placeholder models"""
        return get_field_from_db(obj, 'name', f"Campaign {obj.id}", 'loyalty_campaign')
    
    def get_status(self, obj):
        """Get status field, handling placeholder models"""
        return get_field_from_db(obj, 'status', 'draft', 'loyalty_campaign')
    
    def get_description(self, obj):
        """Get description field, handling placeholder models"""
        return get_field_from_db(obj, 'description', '', 'loyalty_campaign')
    
    def update(self, instance, validated_data):
        """Update campaign, handling placeholder models with raw SQL"""
        # Get data from request for SerializerMethodFields
        update_fields = {}
        
        # Get from request.data (for SerializerMethodFields which are read-only)
        if hasattr(self, 'context') and 'request' in self.context:
            request_data = self.context['request'].data
            for field in ['name', 'status', 'description']:
                if field in request_data:
                    update_fields[field] = request_data[field]
        
        # Get from validated_data (for regular fields)
        for field in ['segment', 'offer_id', 'start_date', 'end_date', 'offer_config', 
                      'eligibility_rules', 'daily_cap', 'total_cap', 'priority']:
            if field in validated_data:
                value = validated_data.pop(field)
                if hasattr(value, 'id'):
                    update_fields[f'{field}_id'] = value.id
                else:
                    update_fields[field] = value
        
        if update_fields:
            save_fields_to_db(instance, update_fields, 'loyalty_campaign')
        
        return instance


class CampaignExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignExecution
        fields = '__all__'


# ============================================================================
# SEGMENTATION
# ============================================================================

class SegmentSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    rules = serializers.SerializerMethodField()
    
    class Meta:
        model = Segment
        fields = '__all__'
        extra_kwargs = {
            'rules': {'write_only': False},  # Allow writing to rules field
        }
    
    def get_name(self, obj):
        """Get name field, handling placeholder models"""
        # Try loyalty_segment first, then segment
        value = get_field_from_db(obj, 'name', None, 'loyalty_segment')
        return value if value is not None else get_field_from_db(obj, 'name', f"Segment {obj.id}", 'segment')
    
    def get_description(self, obj):
        """Get description field, handling placeholder models"""
        value = get_field_from_db(obj, 'description', None, 'loyalty_segment')
        return value if value is not None else get_field_from_db(obj, 'description', '', 'segment')
    
    def get_is_active(self, obj):
        """Get is_active field, handling placeholder models"""
        value = get_field_from_db(obj, 'is_active', None, 'loyalty_segment')
        return value if value is not None else get_field_from_db(obj, 'is_active', True, 'segment')
    
    def get_rules(self, obj):
        """Get rules field for Segment by reading the real DB table directly.

        We **bypass** the placeholder model and `get_field_from_db` because the
        ORM model metadata (managed / db_table) does not match the real table
        (`loyalty_segment`), which caused us to always get `None`.
        """
        import json
        import logging
        from django.db import connection

        logger = logging.getLogger(__name__)

        try:
            # Always read from the actual loyalty_segment table
            table_name = 'loyalty_segment'
            with connection.cursor() as cursor:
                cursor.execute(
                    f'SELECT rules FROM "{table_name}" WHERE id = %s',
                    [obj.id],
                )
                row = cursor.fetchone()

            if not row:
                logger.debug(f"No row found in {table_name} for segment {obj.id}")
                return []

            rules_value = row[0]
            logger.debug(
                f"Raw rules_value from table {table_name} for segment {obj.id}: "
                f"{type(rules_value)} - {rules_value}"
            )

            # If it's a string, parse it as JSON
            if isinstance(rules_value, str):
                rules_value = rules_value.strip()
                if not rules_value:
                    return []
                try:
                    rules_value = json.loads(rules_value)
                    logger.debug(f"Parsed rules_value from string: {rules_value}")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(
                        f"Failed to parse rules JSON string for segment {obj.id}: {e}"
                    )
                    return []

            # Handle None
            if rules_value is None:
                return []

            # Ensure it's a list
            if not isinstance(rules_value, list):
                if isinstance(rules_value, dict) and rules_value:
                    rules_value = [rules_value]
                else:
                    logger.debug(
                        f"rules_value is not list/dict after parsing: "
                        f"{type(rules_value)}"
                    )
                    return []

            # Normalize to new format: {name: string, rule: object}
            normalized_rules = []
            for idx, rule in enumerate(rules_value):
                if not rule:
                    continue

                # New format: {name: "...", rule: {...}}
                if isinstance(rule, dict) and 'name' in rule and 'rule' in rule:
                    normalized_rules.append(
                        {
                            'name': rule.get('name', f'Rule {idx + 1}'),
                            'rule': rule.get('rule', {}),
                        }
                    )
                # Old format: just JSONLogic object
                elif isinstance(rule, dict) and rule:
                    normalized_rules.append(
                        {
                            'name': f'Rule {idx + 1}',
                            'rule': rule,
                        }
                    )
                # String JSON – try to parse
                elif isinstance(rule, str):
                    try:
                        parsed = json.loads(rule)
                        if parsed:
                            normalized_rules.append(
                                {
                                    'name': f'Rule {idx + 1}',
                                    'rule': parsed,
                                }
                            )
                    except Exception:
                        continue

            logger.info(
                f"Returning {len(normalized_rules)} normalized rules for segment {obj.id}"
            )
            return normalized_rules
        except Exception as e:
            logger.error(f"Error loading rules for segment {obj.id}: {e}", exc_info=True)
            return []
    
    def get_member_count(self, obj):
        """Get member count, handling placeholder models with raw SQL"""
        from loyalty.models_khaywe import SegmentMember
        
        # Check if SegmentMember is a placeholder model
        if hasattr(SegmentMember._meta, 'managed') and SegmentMember._meta.managed is False:
            # Use raw SQL to count members
            try:
                from django.db import connection
                table_name = 'loyalty_segmentmember'
                
                with connection.cursor() as cursor:
                    # Check which column exists for segment reference
                    if connection.vendor == 'sqlite':
                        cursor.execute(f"PRAGMA table_info('{table_name}')")
                        cols = [c[1] for c in cursor.fetchall()]
                    else:
                        cursor.execute(
                            "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
                            [table_name]
                        )
                        cols = [c[0] for c in cursor.fetchall()]
                    
                    seg_col = 'segment_id' if 'segment_id' in cols else 'segment'
                    
                    # Count active members
                    if connection.vendor == 'sqlite':
                        cursor.execute(
                            f'SELECT COUNT(*) FROM "{table_name}" WHERE {seg_col} = ? AND is_active = 1',
                            [obj.id]
                        )
                    else:
                        cursor.execute(
                            f'SELECT COUNT(*) FROM "{table_name}" WHERE {seg_col} = %s AND is_active = true',
                            [obj.id]
                        )
                    
                    count = cursor.fetchone()[0]
                    return count
            except Exception as e:
                logger.warning(f"Error counting segment members via raw SQL: {e}")
                return 0
        
        # ORM path for managed models
        try:
            if hasattr(obj, 'members'):
                return obj.members.filter(is_active=True).count()
            return SegmentMember.objects.filter(segment=obj, is_active=True).count()
        except (AttributeError, Exception):
            return 0
    
    def create(self, validated_data):
        """Create segment, handling placeholder models"""
        # Get rules from initial_data since it's a SerializerMethodField (read-only by default)
        rules = self.initial_data.get('rules', [])
        if not rules:
            rules = validated_data.pop('rules', [])
        
        # Extract fields that need to be saved to database
        name = validated_data.pop('name', None)
        description = validated_data.pop('description', '')
        is_active = validated_data.pop('is_active', True)
        is_dynamic = validated_data.pop('is_dynamic', True)
        is_rfm = validated_data.pop('is_rfm', False)
        rfm_config = validated_data.pop('rfm_config', {})
        program_id = validated_data.pop('program', None)
        
        # Create segment object (will have id)
        segment = Segment.objects.create(**validated_data)
        
        # Save fields directly to database
        self._save_segment_fields_to_db(segment, {
            'name': name or f"Segment {segment.id}",
            'description': description,
            'is_active': is_active,
            'is_dynamic': is_dynamic,
            'is_rfm': is_rfm,
            'rules': rules,
            'rfm_config': rfm_config,
            'program_id': program_id.id if program_id else None,
        })
        
        return segment
    
    def update(self, instance, validated_data):
        """Update segment, handling placeholder models"""
        import logging
        import sys
        logger = logging.getLogger(__name__)
        
        # DEBUG: Log everything we have access to - use print as fallback
        print(f"\n{'='*60}")
        print(f"=== UPDATE CALLED FOR SEGMENT {instance.id} ===")
        print(f"{'='*60}\n")
        logger.info(f"=== UPDATE CALLED FOR SEGMENT {instance.id} ===")
        has_context = hasattr(self, 'context')
        print(f"Has context: {has_context}")
        logger.info(f"Has context: {has_context}")
        
        if has_context:
            context_keys = list(self.context.keys())
            print(f"Context keys: {context_keys}")
            logger.info(f"Context keys: {context_keys}")
            
            if 'request' in self.context:
                request = self.context['request']
                print(f"Request method: {request.method}")
                print(f"Request data type: {type(request.data)}")
                print(f"Request data: {request.data}")
                logger.info(f"Request method: {request.method}")
                logger.info(f"Request data type: {type(request.data)}")
                
                if hasattr(request.data, 'keys'):
                    data_keys = list(request.data.keys())
                    print(f"Request data keys: {data_keys}")
                    logger.info(f"Request data keys: {data_keys}")
                    
                    if 'rules' in request.data:
                        rules_from_data = request.data['rules']
                        print(f"*** FOUND RULES IN request.data: {rules_from_data} ***")
                        logger.info(f"*** FOUND RULES IN request.data: {rules_from_data} ***")
                
                if hasattr(request.data, 'get'):
                    rules_via_get = request.data.get('rules')
                    print(f"Request.data.get('rules'): {rules_via_get}")
                    logger.info(f"Request.data.get('rules'): {rules_via_get}")
        
        has_initial_data = hasattr(self, 'initial_data')
        print(f"Has initial_data: {has_initial_data}")
        logger.info(f"Has initial_data: {has_initial_data}")
        
        if has_initial_data:
            if isinstance(self.initial_data, dict):
                initial_keys = list(self.initial_data.keys())
                print(f"Initial_data keys: {initial_keys}")
                logger.info(f"Initial_data keys: {initial_keys}")
                
                if 'rules' in self.initial_data:
                    rules_from_initial = self.initial_data['rules']
                    print(f"*** FOUND RULES IN initial_data: {rules_from_initial} ***")
                    logger.info(f"*** FOUND RULES IN initial_data: {rules_from_initial} ***")
            else:
                print(f"Initial_data type: {type(self.initial_data)}")
                logger.info(f"Initial_data type: {type(self.initial_data)}")
        
        validated_keys = list(validated_data.keys())
        print(f"Validated_data keys: {validated_keys}")
        logger.info(f"Validated_data keys: {validated_keys}")
        
        # Get rules from request.data directly - SerializerMethodField is read-only, so DRF ignores it
        rules = None
        
        # Method 1: Get from request context (most reliable)
        if hasattr(self, 'context') and 'request' in self.context:
            request = self.context['request']
            if hasattr(request, 'data'):
                # DRF request.data can be QueryDict or dict-like
                # Try direct access first
                try:
                    if 'rules' in request.data:
                        rules = request.data['rules']
                        # Handle QueryDict - might return list if multiple values
                        if isinstance(rules, list):
                            # If it's a list of strings (JSON strings), parse them
                            import json
                            parsed_rules = []
                            for rule_item in rules:
                                if isinstance(rule_item, str):
                                    try:
                                        parsed_rules.append(json.loads(rule_item))
                                    except:
                                        pass
                                else:
                                    # Already a dict/object, keep it
                                    parsed_rules.append(rule_item)
                            rules = parsed_rules if parsed_rules else rules
                        # If it's already a list of dicts, keep it as-is
                        print(f"Extracted rules (should be LIST): {rules} (type: {type(rules)})")
                        logger.info(f"✓ Found rules in request.data for segment {instance.id}: {rules} (type: {type(rules)})")
                except Exception as e:
                    logger.warning(f"Error accessing request.data['rules']: {e}")
                
                # Fallback: try .get() method
                if rules is None and hasattr(request.data, 'get'):
                    try:
                        rules = request.data.get('rules')
                        if rules is not None:
                            # Handle QueryDict list - keep as list!
                            if isinstance(rules, list):
                                import json
                                parsed_rules = []
                                for rule_item in rules:
                                    if isinstance(rule_item, str):
                                        try:
                                            parsed_rules.append(json.loads(rule_item))
                                        except:
                                            pass
                                    else:
                                        parsed_rules.append(rule_item)
                                rules = parsed_rules if parsed_rules else rules
                            print(f"Extracted rules via get() (should be LIST): {rules} (type: {type(rules)})")
                            logger.info(f"✓ Found rules via request.data.get() for segment {instance.id}: {rules}")
                    except Exception as e:
                        logger.warning(f"Error accessing request.data.get('rules'): {e}")
        
        # Method 2: Get from initial_data (fallback)
        if rules is None and hasattr(self, 'initial_data'):
            if isinstance(self.initial_data, dict) and 'rules' in self.initial_data:
                rules = self.initial_data['rules']
                logger.info(f"✓ Found rules in initial_data for segment {instance.id}: {rules}")
        
        # Method 3: Get from validated_data (shouldn't happen for SerializerMethodField)
        if rules is None and 'rules' in validated_data:
            rules = validated_data.pop('rules', None)
            logger.info(f"✓ Found rules in validated_data for segment {instance.id}: {rules}")
        
        # Log what we found - USE PRINT TO GUARANTEE VISIBILITY
        if rules is not None:
            print(f"\n{'='*60}")
            print(f"✓✓✓ SAVING RULES FOR SEGMENT {instance.id}")
            print(f"Rules: {rules}")
            print(f"Type: {type(rules)}")
            print(f"{'='*60}\n")
            logger.info(f"✓✓✓ SAVING rules for segment {instance.id}: {rules} (type: {type(rules)})")
        else:
            print(f"\n{'='*60}")
            print(f"✗✗✗ NO RULES FOUND FOR SEGMENT {instance.id}")
            print(f"Context available: {hasattr(self, 'context')}")
            print(f"Request in context: {'request' in self.context if hasattr(self, 'context') else False}")
            if hasattr(self, 'context') and 'request' in self.context:
                req = self.context['request']
                print(f"Request.data type: {type(req.data)}")
                print(f"Request.data content: {dict(req.data) if hasattr(req.data, 'keys') else req.data}")
            print(f"{'='*60}\n")
            logger.error(f"✗✗✗ NO RULES found in request for segment {instance.id}")
            logger.error(f"  Context available: {hasattr(self, 'context')}")
            logger.error(f"  Request in context: {'request' in self.context if hasattr(self, 'context') else False}")
            if hasattr(self, 'context') and 'request' in self.context:
                req = self.context['request']
                logger.error(f"  Request.data type: {type(req.data)}")
                logger.error(f"  Request.data content: {dict(req.data) if hasattr(req.data, 'keys') else req.data}")
        
        # Extract fields that need to be saved to database
        name = validated_data.pop('name', None)
        description = validated_data.pop('description', None)
        is_active = validated_data.pop('is_active', None)
        is_dynamic = validated_data.pop('is_dynamic', None)
        is_rfm = validated_data.pop('is_rfm', None)
        rfm_config = validated_data.pop('rfm_config', None)
        program_id = validated_data.pop('program', None)
        
        # Update fields directly in database
        update_fields = {}
        if name is not None:
            update_fields['name'] = name
        if description is not None:
            update_fields['description'] = description
        if is_active is not None:
            update_fields['is_active'] = is_active
        if is_dynamic is not None:
            update_fields['is_dynamic'] = is_dynamic
        if is_rfm is not None:
            update_fields['is_rfm'] = is_rfm
        if rfm_config is not None:
            update_fields['rfm_config'] = rfm_config
        # Save rules if provided in request
        if rules is not None:
            update_fields['rules'] = rules
            logger.info(f"Including rules in update_fields: {update_fields.get('rules')}")
        # Don't update rules if not provided (preserve existing)
        if program_id is not None:
            update_fields['program_id'] = program_id.id if hasattr(program_id, 'id') else program_id
        
        if update_fields:
            logger.info(f"Updating segment {instance.id} with fields: {list(update_fields.keys())}")
            self._save_segment_fields_to_db(instance, update_fields)
        
        return instance
    
    def _save_segment_fields_to_db(self, segment, fields_dict):
        """Save segment fields directly to database for placeholder models"""
        from django.db import connection
        import json
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Determine table name - check actual table in database
            table_name = None
            
            # First check if segment._meta has db_table
            if hasattr(segment._meta, 'db_table') and segment._meta.db_table:
                table_name = segment._meta.db_table
            else:
                # Check what tables exist in database
                with connection.cursor() as check_cursor:
                    if connection.vendor == 'sqlite':
                        check_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%segment%' OR name='segment')")
                    else:
                        check_cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%segment%' OR table_name = 'segment'")
                    tables = check_cursor.fetchall()
                    if tables:
                        # Prefer 'segment' or 'loyalty_segment'
                        for table_row in tables:
                            table = table_row[0]
                            if table == 'segment' or table == 'loyalty_segment':
                                table_name = table
                                break
                        if not table_name:
                            table_name = tables[0][0]
            
            # Fallback to default - try loyalty_segment first (PostgreSQL convention)
            if not table_name:
                # Check if loyalty_segment exists
                with connection.cursor() as check_cursor:
                    if connection.vendor == 'sqlite':
                        check_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='loyalty_segment'")
                    else:
                        check_cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'loyalty_segment'")
                    if check_cursor.fetchone():
                        table_name = 'loyalty_segment'
                    else:
                        table_name = 'segment'
            
            logger.info(f"Using table name: {table_name} for segment {segment.id}")
            
            logger.info(f"Saving fields to table {table_name} for segment {segment.id}: {list(fields_dict.keys())}")
            
            with connection.cursor() as cursor:
                # Build UPDATE query
                set_clauses = []
                params = []
                
                for field_name, field_value in fields_dict.items():
                    # Skip None values (but allow empty lists/dicts for rules)
                    if field_value is None:
                        continue
                    
                    # Handle JSON fields
                    if field_name in ['rules', 'rfm_config']:
                        # Normalize rules to new format: [{name: string, rule: object}]
                        if field_name == 'rules' and isinstance(field_value, list):
                            # Ensure all rules have name and rule fields
                            normalized_rules = []
                            for idx, rule_item in enumerate(field_value):
                                if not rule_item:
                                    continue
                                
                                # Already in new format
                                if isinstance(rule_item, dict) and 'name' in rule_item and 'rule' in rule_item:
                                    normalized_rules.append({
                                        'name': rule_item.get('name', f'Rule {idx + 1}'),
                                        'rule': rule_item.get('rule', {})
                                    })
                                # Old format: just JSONLogic object
                                elif isinstance(rule_item, dict):
                                    normalized_rules.append({
                                        'name': f'Rule {idx + 1}',
                                        'rule': rule_item
                                    })
                                elif isinstance(rule_item, str):
                                    try:
                                        parsed = json.loads(rule_item)
                                        normalized_rules.append({
                                            'name': f'Rule {idx + 1}',
                                            'rule': parsed
                                        })
                                    except:
                                        continue
                            
                            field_value_json = json.dumps(normalized_rules)
                            logger.info(f"Saving {len(normalized_rules)} rules in normalized format: {field_value_json[:300]}...")
                        else:
                            # For rfm_config or non-list rules, convert to JSON string
                            if isinstance(field_value, (list, dict)):
                                field_value_json = json.dumps(field_value)
                            elif isinstance(field_value, str):
                                # Already a JSON string, validate it
                                try:
                                    json.loads(field_value)  # Validate JSON
                                    field_value_json = field_value
                                except (json.JSONDecodeError, ValueError):
                                    logger.warning(f"Invalid JSON string for {field_name}, converting")
                                    field_value_json = json.dumps(field_value)
                            else:
                                field_value_json = json.dumps(field_value)
                        
                        set_clauses.append(f'"{field_name}" = ?' if connection.vendor == 'sqlite' else f'"{field_name}" = %s')
                        params.append(field_value_json)
                    # Handle boolean fields
                    elif field_name in ['is_active', 'is_dynamic', 'is_rfm']:
                        set_clauses.append(f'"{field_name}" = ?' if connection.vendor == 'sqlite' else f'"{field_name}" = %s')
                        params.append(1 if field_value else 0)
                    # Handle foreign key fields
                    elif field_name.endswith('_id'):
                        set_clauses.append(f'"{field_name}" = ?' if connection.vendor == 'sqlite' else f'"{field_name}" = %s')
                        params.append(field_value)
                    # Handle text fields
                    else:
                        set_clauses.append(f'"{field_name}" = ?' if connection.vendor == 'sqlite' else f'"{field_name}" = %s')
                        params.append(str(field_value))
                
                if set_clauses:
                    # Add updated_at timestamp
                    from django.utils import timezone
                    set_clauses.append('"updated_at" = ?' if connection.vendor == 'sqlite' else '"updated_at" = %s')
                    params.append(timezone.now())
                    
                    # Execute UPDATE
                    params.append(segment.id)  # WHERE id = ?
                    query = f'UPDATE "{table_name}" SET {", ".join(set_clauses)} WHERE id = ?' if connection.vendor == 'sqlite' else f'UPDATE "{table_name}" SET {", ".join(set_clauses)} WHERE id = %s'
                    
                    logger.info(f"Executing UPDATE query for segment {segment.id} with {len(set_clauses)} fields")
                    cursor.execute(query, params)
                    
                    # Verify the update worked (especially for rules)
                    if 'rules' in fields_dict:
                        if connection.vendor == 'sqlite':
                            cursor.execute(f'SELECT rules FROM "{table_name}" WHERE id = ?', [segment.id])
                        else:
                            cursor.execute(f'SELECT rules FROM "{table_name}" WHERE id = %s', [segment.id])
                        result = cursor.fetchone()
                        if result:
                            saved_rules = result[0]
                            logger.info(f"Verified rules saved for segment {segment.id}: {saved_rules[:200] if saved_rules else 'NULL'}...")
                        else:
                            logger.warning(f"Could not verify rules save for segment {segment.id}")
                    
        except Exception as e:
            logger.error(f"Error saving segment fields to database: {e}", exc_info=True)
            raise serializers.ValidationError(f"Failed to save segment: {str(e)}")


class SegmentMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = SegmentMember
        fields = '__all__'


class SegmentSnapshotSerializer(serializers.ModelSerializer):
    snapshot_date = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = SegmentSnapshot
        fields = ['id', 'segment', 'snapshot_date', 'member_count', 'created_at']
    
    def get_snapshot_date(self, obj):
        """Get snapshot_date handling placeholder models"""
        if hasattr(obj, 'snapshot_date') and obj.snapshot_date:
            return obj.snapshot_date
        return get_field_from_db(obj, 'snapshot_date')
    
    def get_member_count(self, obj):
        """Get member_count handling placeholder models"""
        if hasattr(obj, 'member_count') and obj.member_count is not None:
            return obj.member_count
        count = get_field_from_db(obj, 'member_count')
        return count if count is not None else 0
    
    def get_created_at(self, obj):
        """Get created_at handling placeholder models"""
        # created_at might be same as snapshot_date or a separate field
        if hasattr(obj, 'created_at') and obj.created_at:
            return obj.created_at
        created_at = get_field_from_db(obj, 'created_at')
        if created_at:
            return created_at
        # Fall back to snapshot_date
        return self.get_snapshot_date(obj)


# ============================================================================
# GAMIFICATION
# ============================================================================

class MissionSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Mission
        fields = '__all__'
    
    def get_name(self, obj):
        """Get name field, handling placeholder models"""
        return get_field_from_db(obj, 'name', f"Mission {obj.id}", 'loyalty_mission')
    
    def get_description(self, obj):
        """Get description field, handling placeholder models"""
        return get_field_from_db(obj, 'description', '', 'loyalty_mission')
    
    def get_status(self, obj):
        """Get status from is_active field (tables use is_active, not status)"""
        is_active = get_field_from_db(obj, 'is_active', True, 'loyalty_mission')
        return 'active' if is_active else 'inactive'
    
    def update(self, instance, validated_data):
        """Update mission, handling placeholder models with raw SQL"""
        update_fields = {}
        
        # Get from request.data (for SerializerMethodFields)
        if hasattr(self, 'context') and 'request' in self.context:
            request_data = self.context['request'].data
            for field in ['name', 'description']:
                if field in request_data:
                    update_fields[field] = request_data[field]
            # Map status -> is_active
            if 'status' in request_data:
                update_fields['is_active'] = request_data['status'] == 'active'
        
        # Get from validated_data (for regular fields)
        for field in ['program', 'mission_type', 'target_value', 'reward_points', 
                      'start_date', 'end_date', 'config', 'is_active']:
            if field in validated_data:
                value = validated_data.pop(field)
                if hasattr(value, 'id'):
                    update_fields[f'{field}_id'] = value.id
                else:
                    update_fields[field] = value
        
        if update_fields:
            save_fields_to_db(instance, update_fields, 'loyalty_mission')
        
        return instance


class MissionProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionProgress
        fields = '__all__'


class BadgeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Badge
        fields = '__all__'
    
    def get_name(self, obj):
        """Get name field, handling placeholder models"""
        return get_field_from_db(obj, 'name', f"Badge {obj.id}", 'loyalty_badge')
    
    def get_description(self, obj):
        """Get description field, handling placeholder models"""
        return get_field_from_db(obj, 'description', '', 'loyalty_badge')
    
    def get_status(self, obj):
        """Get status from is_active field (tables use is_active, not status)"""
        is_active = get_field_from_db(obj, 'is_active', True, 'loyalty_badge')
        return 'active' if is_active else 'inactive'
    
    def update(self, instance, validated_data):
        """Update badge, handling placeholder models with raw SQL"""
        update_fields = {}
        
        # Get from request.data (for SerializerMethodFields)
        if hasattr(self, 'context') and 'request' in self.context:
            request_data = self.context['request'].data
            for field in ['name', 'description']:
                if field in request_data:
                    update_fields[field] = request_data[field]
            # Map status -> is_active
            if 'status' in request_data:
                update_fields['is_active'] = request_data['status'] == 'active'
        
        # Get from validated_data (for regular fields)
        for field in ['program', 'badge_type', 'icon_url', 'criteria', 'points_value', 'is_active']:
            if field in validated_data:
                value = validated_data.pop(field)
                if hasattr(value, 'id'):
                    update_fields[f'{field}_id'] = value.id
                else:
                    update_fields[field] = value
        
        if update_fields:
            save_fields_to_db(instance, update_fields, 'loyalty_badge')
        
        return instance


class BadgeAwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = BadgeAward
        fields = '__all__'


class LeaderboardSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Leaderboard
        fields = '__all__'
    
    def get_name(self, obj):
        """Get name field, handling placeholder models"""
        return get_field_from_db(obj, 'name', f"Leaderboard {obj.id}", 'loyalty_leaderboard')
    
    def get_description(self, obj):
        """Get description field, handling placeholder models"""
        return get_field_from_db(obj, 'description', '', 'loyalty_leaderboard')
    
    def get_status(self, obj):
        """Get status from is_active field (tables use is_active, not status)"""
        is_active = get_field_from_db(obj, 'is_active', True, 'loyalty_leaderboard')
        return 'active' if is_active else 'inactive'
    
    def update(self, instance, validated_data):
        """Update leaderboard, handling placeholder models with raw SQL"""
        update_fields = {}
        
        # Get from request.data (for SerializerMethodFields)
        if hasattr(self, 'context') and 'request' in self.context:
            request_data = self.context['request'].data
            for field in ['name', 'description']:
                if field in request_data:
                    update_fields[field] = request_data[field]
            # Map status -> is_active
            if 'status' in request_data:
                update_fields['is_active'] = request_data['status'] == 'active'
        
        # Get from validated_data (for regular fields)
        for field in ['program', 'metric', 'period', 'config', 'is_active']:
            if field in validated_data:
                value = validated_data.pop(field)
                if hasattr(value, 'id'):
                    update_fields[f'{field}_id'] = value.id
                else:
                    update_fields[field] = value
        
        if update_fields:
            save_fields_to_db(instance, update_fields, 'loyalty_leaderboard')
        
        return instance


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaderboardEntry
        fields = '__all__'


class StreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Streak
        fields = '__all__'


# ============================================================================
# JOURNEY BUILDER
# ============================================================================

class JourneyNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JourneyNode
        fields = '__all__'


class JourneyEdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JourneyEdge
        fields = '__all__'


class JourneySerializer(serializers.ModelSerializer):
    nodes = JourneyNodeSerializer(many=True, read_only=True)
    edges = JourneyEdgeSerializer(many=True, read_only=True)
    structure = serializers.JSONField(required=False, allow_null=True)
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Journey
        fields = '__all__'
    
    def get_name(self, obj):
        """Get name field, handling placeholder models"""
        return get_field_from_db(obj, 'name', f"Journey {obj.id}", 'loyalty_journey')
    
    def get_description(self, obj):
        """Get description field, handling placeholder models"""
        return get_field_from_db(obj, 'description', '', 'loyalty_journey')
    
    def get_status(self, obj):
        """Get status from is_active field (tables use is_active, not status)"""
        is_active = get_field_from_db(obj, 'is_active', True, 'loyalty_journey')
        return 'active' if is_active else 'inactive'
    
    def update(self, instance, validated_data):
        """Update journey, handling placeholder models with raw SQL"""
        update_fields = {}
        
        # Get from request.data (for SerializerMethodFields)
        if hasattr(self, 'context') and 'request' in self.context:
            request_data = self.context['request'].data
            for field in ['name', 'description']:
                if field in request_data:
                    update_fields[field] = request_data[field]
            # Map status -> is_active
            if 'status' in request_data:
                update_fields['is_active'] = request_data['status'] == 'active'
        
        # Get from validated_data (for regular fields)
        for field in ['program', 'segment', 'trigger_event', 'structure', 'config', 'is_active']:
            if field in validated_data:
                value = validated_data.pop(field)
                if hasattr(value, 'id'):
                    update_fields[f'{field}_id'] = value.id
                else:
                    update_fields[field] = value
        
        if update_fields:
            save_fields_to_db(instance, update_fields, 'loyalty_journey')
        
        return instance


class JourneyExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JourneyExecution
        fields = '__all__'


# ============================================================================
# A/B TESTING
# ============================================================================

class ExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiment
        fields = '__all__'


class ExperimentAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentAssignment
        fields = '__all__'


class HoldoutGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoldoutGroup
        fields = '__all__'


# ============================================================================
# PARTNER/COALITION
# ============================================================================

class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = '__all__'


class PartnerProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerProgram
        fields = '__all__'


class PartnerSettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerSettlement
        fields = '__all__'


class CoalitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coalition
        fields = '__all__'


# ============================================================================
# RBAC
# ============================================================================

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'


class RolePermissionSerializer(serializers.ModelSerializer):
    permission = PermissionSerializer(read_only=True)
    
    class Meta:
        model = RolePermission
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    permissions = RolePermissionSerializer(many=True, read_only=True, source='permissions')
    
    class Meta:
        model = Role
        fields = '__all__'


class UserRoleSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    
    class Meta:
        model = UserRole
        fields = '__all__'


class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalWorkflow
        fields = '__all__'


class ApprovalDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalDecision
        fields = '__all__'


class ApprovalRequestSerializer(serializers.ModelSerializer):
    decisions = ApprovalDecisionSerializer(many=True, read_only=True, source='decisions')
    
    class Meta:
        model = ApprovalRequest
        fields = '__all__'


# ============================================================================
# POINTS EXPIRY & CAPS
# ============================================================================

class PointsExpiryRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsExpiryRule
        fields = '__all__'


class PointsExpiryEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsExpiryEvent
        fields = '__all__'


class EarnCapSerializer(serializers.ModelSerializer):
    class Meta:
        model = EarnCap
        fields = '__all__'


class CapUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapUsage
        fields = '__all__'


# ============================================================================
# GAMIFICATION DATA SOURCES
# ============================================================================

class DataSourceConfigSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='source_name', required=False)
    
    class Meta:
        model = DataSourceConfig
        fields = '__all__'
        extra_kwargs = {
            'source_name': {'required': False},
        }
    
    def validate(self, data):
        # If 'name' is provided, use it as source_name
        if 'name' in self.initial_data:
            data['source_name'] = self.initial_data['name']
        return data


class CustomerEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerEvent
        fields = '__all__'


class CustomerBehaviorScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerBehaviorScore
        fields = '__all__'


class MissionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionTemplate
        fields = '__all__'

