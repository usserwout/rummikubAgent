



## Known problems
#### `Error solving ILP: PULP_CBC_CMD: Not Available (check permissions on /Users/.../lib/python3.12/site-packages/pulp/solverdir/cbc/osx/arm64/cbc)`
This error may occur when you use a apple silicon. To solve this go to `/Users/.../lib/python3.12/site-packages/pulp/solverdir/cbc/osx` and rename the `64` to `arm64`.  