# Complete Full Example

This source fixture demonstrates all five SDR stages. The probe processes only hard-coded invented
strings, declares `verify.action: run`, uses an argument vector, and prints one deterministic marker.
The runner replaces the generic Python executable with its own `sys.executable` in the temporary
copy before explicit verification. No shell or network is used.
