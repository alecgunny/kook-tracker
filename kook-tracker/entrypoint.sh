#!/bin/bash

set -e

echo $RDS_HOSTNAME

flask db init
flask db upgrade
flask run --host=0.0.0.0