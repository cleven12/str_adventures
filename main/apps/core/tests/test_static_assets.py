"""Guardrails for compiled Tailwind + cache-busted static URLs."""

from pathlib import Path

from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import SimpleTestCase

from apps.core.context_processors import _static_asset_version, site_settings


class StaticCssBuildTests(SimpleTestCase):
    """Fail CI if the Tailwind bundle is missing, tiny, or not cache-busted in base."""

    def test_compiled_tailwind_exists_and_is_full_build(self):
        css_path = Path(settings.BASE_DIR) / "static" / "dist" / "tailwind.css"
        self.assertTrue(css_path.is_file(), f"Missing {css_path}; run npm run build:css")
        size = css_path.stat().st_size
        # Hand-curated stub was ~12KB; full production build is typically 80KB+.
        self.assertGreaterEqual(
            size,
            50_000,
            f"tailwind.css is only {size} bytes — expected a full build (>= 50KB)",
        )
        css = css_path.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("--tw-border-spacing", css)
        self.assertIn("font-display", css)

    def test_base_template_uses_cache_busted_css(self):
        base = Path(settings.BASE_DIR) / "templates" / "base.html"
        text = base.read_text(encoding="utf-8")
        self.assertIn("STATIC_ASSET_VERSION", text)
        self.assertIn("dist/tailwind.css", text)
        self.assertIn("?v={{ STATIC_ASSET_VERSION", text)

    def test_static_asset_version_is_content_hash(self):
        _static_asset_version.cache_clear()
        version = _static_asset_version()
        self.assertNotEqual(version, "1")
        self.assertRegex(version, r"^[a-f0-9]{12}$")

    @patch("apps.core.context_processors.SiteSettings.objects")
    def test_site_settings_exposes_static_asset_version(self, mock_objects):
        mock_objects.first.return_value = None
        _static_asset_version.cache_clear()
        req = MagicMock()
        req.session = {"currency": "USD"}
        ctx = site_settings(req)
        self.assertIn("STATIC_ASSET_VERSION", ctx)
        self.assertEqual(ctx["STATIC_ASSET_VERSION"], _static_asset_version())
