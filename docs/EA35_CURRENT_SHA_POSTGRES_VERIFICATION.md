# EA-35 Current-SHA PostgreSQL verification trigger

This marker exists solely to trigger the branch PostgreSQL production smoke workflows against the current canonical production runtime and migration runner.

Required interpretation: this file is not evidence by itself. Evidence is the GitHub Actions result for the commit that adds this marker.


Current-SHA re-verification trigger: execute the canonical PostgreSQL production gates against this commit; prior successful SHAs are not sufficient for final lock.
