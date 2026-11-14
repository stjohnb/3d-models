// =====================================
// Test print - Male connection (shaft + collar)
// Quick print to verify fit against female socket
// =====================================

include <_connection.scad>

$fn = 64;

// Base plate so it prints flat (collar-down)
// The collar sits on the bed, shaft points up
collar();
sq_shaft();
