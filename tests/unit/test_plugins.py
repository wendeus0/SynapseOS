from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from synapse_os.plugins import (
    PluginManifest,
    PluginRegistry,
    PluginLoadError,
    HookSpec,
    HOOK_TYPES,
)


class TestHookSpec:
    def test_hook_spec_create(self):
        spec = HookSpec(name="test", hook_type="pre_step", handler=MagicMock())
        assert spec.name == "test"
        assert spec.hook_type == "pre_step"

    def test_valid_hook_types(self):
        assert "pre_step" in HOOK_TYPES
        assert "post_step" in HOOK_TYPES
        assert "on_run_start" in HOOK_TYPES
        assert "on_run_end" in HOOK_TYPES


class TestPluginManifest:
    def test_create_manifest(self):
        manifest = PluginManifest(name="test-plugin", version="1.0.0")
        assert manifest.name == "test-plugin"
        assert manifest.version == "1.0.0"
        assert manifest.enabled is True

    def test_manifest_default_enabled(self):
        manifest = PluginManifest(name="test", version="0.1.0")
        assert manifest.enabled is True

    def test_manifest_with_hooks(self):
        manifest = PluginManifest(
            name="test",
            version="1.0.0",
            hooks=["pre_step", "post_step"],
        )
        assert "pre_step" in manifest.hooks
        assert "post_step" in manifest.hooks


class TestPluginRegistry:
    def test_singleton_pattern(self):
        registry1 = PluginRegistry()
        registry2 = PluginRegistry()
        assert registry1 is registry2

    def test_register_plugin(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        manifest = PluginManifest(name="test-plugin", version="1.0.0")
        registry.register(manifest)
        assert "test-plugin" in registry.list_plugins()

    def test_register_duplicate_raises(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        manifest = PluginManifest(name="dup-plugin", version="1.0.0")
        registry.register(manifest)
        with pytest.raises(PluginLoadError, match="already registered"):
            registry.register(manifest)

    def test_unregister_plugin(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        manifest = PluginManifest(name="unreg-plugin", version="1.0.0")
        registry.register(manifest)
        registry.unregister("unreg-plugin")
        assert "unreg-plugin" not in registry.list_plugins()

    def test_unregister_unknown_raises(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        with pytest.raises(PluginLoadError, match="not found"):
            registry.unregister("nonexistent")

    def test_get_plugin(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        manifest = PluginManifest(name="get-plugin", version="2.0.0")
        registry.register(manifest)
        retrieved = registry.get_plugin("get-plugin")
        assert retrieved is not None
        assert retrieved.name == "get-plugin"

    def test_get_plugin_not_found(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        assert registry.get_plugin("nonexistent") is None

    def test_list_plugins(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        registry.register(PluginManifest(name="p1", version="1.0.0"))
        registry.register(PluginManifest(name="p2", version="1.0.0"))
        plugins = registry.list_plugins()
        assert "p1" in plugins
        assert "p2" in plugins

    def test_enable_disable_plugin(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        manifest = PluginManifest(name="toggle-plugin", version="1.0.0")
        registry.register(manifest)
        registry.disable_plugin("toggle-plugin")
        assert not registry.get_plugin("toggle-plugin").enabled
        registry.enable_plugin("toggle-plugin")
        assert registry.get_plugin("toggle-plugin").enabled

    def test_get_handlers_for_hook(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        handler = MagicMock()
        manifest = PluginManifest(
            name="handler-plugin",
            version="1.0.0",
            hooks=["pre_step"],
        )
        registry.register(manifest)
        registry.register_hook("handler-plugin", "pre_step", handler)
        handlers = registry.get_handlers("pre_step")
        assert handler in handlers

    def test_get_handlers_empty_for_unknown_hook(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        handlers = registry.get_handlers("on_run_start")
        assert handlers == []

    def test_hook_type_validation(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        manifest = PluginManifest(name="val-plugin", version="1.0.0")
        registry.register(manifest)
        with pytest.raises(ValueError, match="Unknown hook type"):
            registry.register_hook("val-plugin", "invalid_hook", MagicMock())

    def test_load_plugins_discovers_entry_points(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        mock_ep = MagicMock()
        mock_ep.name = "discovered-plugin"
        mock_ep.load.return_value.hook_manifest.return_value = PluginManifest(
            name="discovered-plugin", version="0.1.0", hooks=["pre_step"]
        )
        with patch("synapse_os.plugins.entry_points") as mock_eps:
            mock_eps.return_value = [mock_ep]
            registry.load_plugins()
        assert "discovered-plugin" in registry.list_plugins()

    def test_load_plugins_handles_missing_manifest(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        mock_ep = MagicMock()
        mock_ep.name = "no-manifest-plugin"
        mock_ep.load.return_value.hook_manifest = None
        with patch("synapse_os.plugins.entry_points") as mock_eps:
            mock_eps.return_value = [mock_ep]
            registry.load_plugins()
        assert "no-manifest-plugin" not in registry.list_plugins()

    def test_is_loaded(self):
        registry = PluginRegistry()
        registry._plugins.clear()
        assert registry.is_loaded("test") is False
        registry.register(PluginManifest(name="test", version="1.0.0"))
        assert registry.is_loaded("test") is True
