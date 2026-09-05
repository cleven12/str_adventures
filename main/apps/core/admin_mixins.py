"""Dependency-free JSON bulk-import for the Django admin.

Add ``JSONImportMixin`` to any ``ModelAdmin`` to get an "Import JSON" button on
the changelist. Staff upload a JSON array of objects; each object upserts one
record matched by ``json_import_key`` (default ``slug``). Only concrete, scalar
fields are written — foreign keys, many-to-many and image/file fields are left
for staff to set in the admin. The whole import runs in one transaction, so any
error rolls the batch back with no partial writes.
"""
import json

from django import forms
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path, reverse
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldBooleanSwitchWidget


class JSONImportForm(forms.Form):
    json_file = forms.FileField(
        label="JSON file",
        help_text="A JSON array of objects (or a single object).",
        widget=UnfoldAdminFileFieldWidget,
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=True,
        label="Dry run",
        help_text="Preview the import without saving anything.",
        widget=UnfoldBooleanSwitchWidget,
    )


class JSONImportMixin:
    change_list_template = "admin/json_import_changelist.html"
    json_import_key = "slug"

    # ── URL wiring ──────────────────────────────────────────
    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        custom = [
            path(
                "import-json/",
                self.admin_site.admin_view(self.import_json_view),
                name="%s_%s_import_json" % info,
            ),
        ]
        return custom + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        info = self.model._meta.app_label, self.model._meta.model_name
        extra_context["import_json_url"] = reverse("admin:%s_%s_import_json" % info)
        return super().changelist_view(request, extra_context=extra_context)

    # ── Which fields can be written from JSON ───────────────
    def _importable_fields(self):
        names = []
        for f in self.model._meta.get_fields():
            if not getattr(f, "concrete", False) or f.auto_created:
                continue
            if f.many_to_many or f.one_to_many or f.is_relation:
                continue
            internal = f.get_internal_type()
            if "File" in internal or "Image" in internal:
                continue
            if f.__class__.__name__ == "CloudinaryField":
                continue
            if f.name in ("id", "pk"):
                continue
            names.append(f.name)
        return names

    # ── The import view ─────────────────────────────────────
    def import_json_view(self, request):
        if request.method == "POST":
            form = JSONImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    raw = request.FILES["json_file"].read().decode("utf-8")
                    data = json.loads(raw)
                    if isinstance(data, dict):
                        data = [data]
                    if not isinstance(data, list):
                        raise ValueError("Top-level JSON must be a list of objects.")
                except Exception as exc:
                    messages.error(request, f"Could not read JSON: {exc}")
                    return redirect(request.path)

                key = self.json_import_key
                model_field_names = {f.name for f in self.model._meta.get_fields()}
                has_key = key in model_field_names
                allowed = set(self._importable_fields())
                created = updated = 0
                errors = []
                dry_run = form.cleaned_data.get("dry_run", False)

                try:
                    with transaction.atomic():
                        sid = transaction.savepoint()
                        for i, row in enumerate(data, start=1):
                            if not isinstance(row, dict):
                                errors.append(f"Row {i}: not a JSON object")
                                raise ValueError("bad row")
                            defaults = {k: v for k, v in row.items()
                                        if k in allowed and k != key}
                            try:
                                if has_key and row.get(key):
                                    _, was_created = self.model.objects.update_or_create(
                                        **{key: row[key]}, defaults=defaults
                                    )
                                else:
                                    self.model.objects.create(**defaults)
                                    was_created = True
                                created += 1 if was_created else 0
                                updated += 0 if was_created else 1
                            except Exception as exc:
                                errors.append(f"Row {i}: {exc}")
                                raise
                        if dry_run:
                            transaction.savepoint_rollback(sid)
                        else:
                            transaction.savepoint_commit(sid)
                except Exception:
                    messages.error(
                        request,
                        "Import rolled back — nothing saved. "
                        + " | ".join(errors[:5]),
                    )
                    return redirect(request.path)

                label = "previewed" if dry_run else "saved"
                messages.success(
                    request, f"JSON import complete: {created} created, {updated} updated ({label})."
                )
                return redirect("..")
        else:
            form = JSONImportForm()

        context = {
            **self.admin_site.each_context(request),
            "title": f"Import {self.model._meta.verbose_name_plural} from JSON",
            "opts": self.model._meta,
            "form": form,
            "key_field": self.json_import_key,
            "importable_fields": sorted(self._importable_fields()),
        }
        return render(request, "admin/json_import_form.html", context)
