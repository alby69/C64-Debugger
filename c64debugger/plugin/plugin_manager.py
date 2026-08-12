import os
import sys
import importlib.util
import logging
from typing import Dict, Any, List, Optional, Callable, Set

logger = logging.getLogger("C64DebuggerPlugin")

class C64DebuggerPlugin:
    """
    Base class for all C64 Debugger plugins.
    Plugins can hook into various debugger events and register custom CLI commands.
    """
    name: str = "BasePlugin"
    description: str = "Base debugger plugin description"
    version: str = "1.0.0"

    def __init__(self) -> None:
        self.manager: Optional["C64PluginManager"] = None

    def on_plugin_load(self, manager: "C64PluginManager") -> None:
        """Called when the plugin is loaded."""
        self.manager = manager

    def on_plugin_unload(self, manager: "C64PluginManager") -> None:
        """Called when the plugin is unloaded."""
        self.manager = None

    def pre_breakpoint(self, addr: int, regs: Dict[str, Any]) -> None:
        """Hook executed BEFORE a breakpoint is hit or processed."""
        pass

    def post_breakpoint(self, addr: int, regs: Dict[str, Any]) -> None:
        """Hook executed AFTER a breakpoint is hit or processed."""
        pass

    def pre_step(self, regs: Dict[str, Any]) -> None:
        """Hook executed BEFORE a step is taken."""
        pass

    def post_step(self, regs: Dict[str, Any]) -> None:
        """Hook executed AFTER a step is taken."""
        pass

    def on_crash(self, crash_report: Dict[str, Any]) -> None:
        """Hook executed when a crash or abnormal CPU state is detected."""
        pass


# Global list of registered batch scripting functions
_registered_scripts: List[Callable[..., Any]] = []

def c64_script(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to mark a function as a runnable C64 Debugger script.
    """
    if func not in _registered_scripts:
        _registered_scripts.append(func)
    return func


class C64PluginManager:
    """
    Manages loading, unloading, and lifecycle events of debugger plugins.
    Also handles custom CLI command registration for plugins.
    """
    def __init__(self, core: Any = None, bridge: Any = None, repl: Any = None) -> None:
        self.core = core
        self.bridge = bridge
        self.repl = repl
        if core is not None:
            core.plugin_manager = self
        self.loaded_plugins: Dict[str, C64DebuggerPlugin] = {}
        # Dynamic commands registered by plugins: command_name -> (handler, help_text)
        self.custom_commands: Dict[str, tuple[Callable[..., Any], str]] = {}

    def set_context(self, core: Any = None, bridge: Any = None, repl: Any = None) -> None:
        """Updates the context objects."""
        if core is not None:
            self.core = core
            core.plugin_manager = self
        if bridge is not None:
            self.bridge = bridge
        if repl is not None:
            self.repl = repl

    def load_plugin(self, filepath: str) -> Optional[C64DebuggerPlugin]:
        """
        Dynamically loads a plugin from a Python file.
        """
        if not os.path.exists(filepath):
            logger.error(f"Plugin file not found: {filepath}")
            return None

        try:
            # Generate unique module name
            module_name = f"c64dbg_plugin_{os.path.splitext(os.path.basename(filepath))[0]}"
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create module spec for {filepath}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Look for classes inheriting from C64DebuggerPlugin
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                        issubclass(attr, C64DebuggerPlugin) and
                        attr is not C64DebuggerPlugin):
                    plugin_class = attr
                    break

            if plugin_class is None:
                logger.error(f"No valid C64DebuggerPlugin class found in {filepath}")
                return None

            plugin_instance = plugin_class()
            p_name = getattr(plugin_instance, "name", plugin_class.__name__)

            if p_name in self.loaded_plugins:
                logger.warning(f"Plugin '{p_name}' is already loaded. Unloading previous instance first.")
                self.unload_plugin(p_name)

            plugin_instance.on_plugin_load(self)
            self.loaded_plugins[p_name] = plugin_instance
            logger.info(f"Loaded plugin: {p_name} v{getattr(plugin_instance, 'version', '1.0.0')}")
            return plugin_instance

        except Exception as e:
            logger.exception(f"Error loading plugin from {filepath}: {e}")
            return None

    def unload_plugin(self, name: str) -> bool:
        """
        Unloads a plugin by name.
        """
        if name not in self.loaded_plugins:
            logger.warning(f"Plugin '{name}' is not loaded.")
            return False

        try:
            plugin = self.loaded_plugins[name]
            plugin.on_plugin_unload(self)
            # Unregister any command registered by this plugin
            commands_to_remove = [cmd_name for cmd_name, (handler, _) in self.custom_commands.items()
                                  if getattr(handler, "__self__", None) == plugin]
            for cmd_name in commands_to_remove:
                self.unregister_command(cmd_name)

            del self.loaded_plugins[name]
            logger.info(f"Unloaded plugin: {name}")
            return True
        except Exception as e:
            logger.exception(f"Error unloading plugin '{name}': {e}")
            return False

    def list_plugins(self) -> Dict[str, C64DebuggerPlugin]:
        """Returns all currently loaded plugins."""
        return self.loaded_plugins

    def register_command(self, name: str, handler: Callable[..., Any], help_text: str = "") -> None:
        """
        Registers a dynamic CLI command that can be invoked via the REPL.
        """
        cmd_name = name.lower().strip()
        self.custom_commands[cmd_name] = (handler, help_text)
        logger.info(f"Registered custom command: {cmd_name}")

        # If REPL is present, dynamically inject a `do_<name>` method
        if self.repl is not None:
            self._inject_cmd_to_repl(cmd_name, handler, help_text)

    def unregister_command(self, name: str) -> None:
        """Unregisters a custom CLI command."""
        cmd_name = name.lower().strip()
        if cmd_name in self.custom_commands:
            del self.custom_commands[cmd_name]
            logger.info(f"Unregistered custom command: {cmd_name}")

            # If REPL is present, remove the dynamically injected method
            if self.repl is not None:
                attr_name = f"do_{cmd_name}"
                if hasattr(self.repl, attr_name):
                    delattr(self.repl, attr_name)

    def trigger_hook(self, hook_name: str, *args, **kwargs) -> None:
        """
        Triggers a lifecycle hook for all loaded plugins.
        """
        for name, plugin in list(self.loaded_plugins.items()):
            hook = getattr(plugin, hook_name, None)
            if hook and callable(hook):
                try:
                    hook(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in hook '{hook_name}' for plugin '{name}': {e}")

    def _inject_cmd_to_repl(self, cmd_name: str, handler: Callable[..., Any], help_text: str) -> None:
        """Helper to inject command dynamically into CMD REPL."""
        def cmd_wrapper(repl_self, arg: str):
            try:
                # Basic parsing: split arguments by space
                args = arg.split() if arg else []
                handler(*args)
            except Exception as e:
                print(f"Error executing custom command '{cmd_name}': {e}")

        cmd_wrapper.__doc__ = help_text or f"Custom plugin command: {cmd_name}"
        setattr(self.repl, f"do_{cmd_name}", cmd_wrapper.__get__(self.repl, self.repl.__class__))
