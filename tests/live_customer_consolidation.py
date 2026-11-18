"""Compatibility entry point for the expanded customer intelligence acceptance.

The generalized check also reconciles the legacy Motor-to-Travel subset and
retention counts/order. Uses real Snowflake reads through the API in process;
no running web server is required.
"""
import runpy

if __name__ == '__main__':
    runpy.run_module('tests.live_product_opportunities',run_name='__main__')
