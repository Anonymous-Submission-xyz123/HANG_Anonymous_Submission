# Natural language intent:
# Dynamic Invocation with Reflection, Uses reflection to dynamically invoke system management functions, allowing for more stealthy execution of commands.

$assembly = [Reflection.Assembly]::LoadWithPartialName('System.Management'); $type = $assembly.GetType('System.Management.ManagementObjectSearcher'); $constructor = $type.GetConstructor(@([string])); $instance = $constructor.Invoke(@('SELECT * FROM Win32_Process')); $method = $type.GetMethod('Get'); $result = $method.Invoke($instance, @())
