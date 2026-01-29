"""
Utility functions for loyalty service.
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# JSONLogic evaluation
try:
    import json_logic
    JSON_LOGIC_AVAILABLE = True
except ImportError:
    JSON_LOGIC_AVAILABLE = False
    json_logic = None
    logger.warning("json-logic-py not available. Rule evaluation disabled.")


def safe_json_logic(rule: Any, data: Dict[str, Any]) -> bool:
    """
    Safely evaluate a JSONLogic rule.
    
    Args:
        rule: JSONLogic rule (dict or list)
        data: Data to evaluate against
    
    Returns:
        Boolean result of evaluation
    """
    # Treat empty / None rule as "always true"
    if not rule:
        return True

    # Local, lightweight evaluator to avoid bugs in some json_logic versions
    def _resolve_var(node: Any, context: Dict[str, Any]) -> Any:
        """
        Resolve a JSONLogic `var` reference or return the literal value.
        Supports:
          - {'var': 'field_name'}
          - direct literals (numbers, strings, bool)
        """
        if isinstance(node, dict) and "var" in node:
            key = node.get("var")
            return context.get(key)
        return node

    def _eval(rule_node: Any, context: Dict[str, Any]) -> Any:
        # Primitives
        if not isinstance(rule_node, dict):
            return rule_node

        # Logical combinators
        if "and" in rule_node:
            return all(_eval(r, context) for r in rule_node.get("and", []))
        if "or" in rule_node:
            return any(_eval(r, context) for r in rule_node.get("or", []))
        if "!" in rule_node:
            return not _eval(rule_node.get("!"), context)

        # Comparison operators
        for op in (">", "<", ">=", "<=", "==", "!="):
            if op in rule_node:
                args = rule_node[op]
                if not isinstance(args, list) or len(args) != 2:
                    return False
                left = _resolve_var(args[0], context)
                right = _resolve_var(args[1], context)
                try:
                    if op == ">":
                        return left > right
                    if op == "<":
                        return left < right
                    if op == ">=":
                        return left >= right
                    if op == "<=":
                        return left <= right
                    if op == "==":
                        return left == right
                    if op == "!=":
                        return left != right
                except Exception:
                    return False

        # "in" operator
        if "in" in rule_node:
            args = rule_node["in"]
            if not isinstance(args, list) or len(args) != 2:
                return False
            item, collection = args
            item_val = _resolve_var(item, context)
            collection_val = _resolve_var(collection, context)
            try:
                if isinstance(collection_val, (list, tuple, set)):
                    return item_val in collection_val
                # Allow \"value in field\" style from VisualRuleBuilder
                if isinstance(collection_val, str):
                    return str(item_val) in collection_val
            except Exception:
                return False

        # Fallback: if we have the json_logic library, try it as a last resort
        if JSON_LOGIC_AVAILABLE:
            try:
                result = json_logic.jsonLogic(rule_node, context)
                return result
            except Exception as e:
                logger.error(
                    f"Error evaluating JSONLogic rule with library: {e}, rule={rule_node}, data={context}"
                )
                return False

        # Unknown structure → fail safe
        return False

    try:
        result = _eval(rule, data)
        # Normalize to boolean
        return bool(result)
    except Exception as e:
        logger.error(f"Error evaluating JSONLogic rule: {e}, rule={rule}, data={data}")
        return False
