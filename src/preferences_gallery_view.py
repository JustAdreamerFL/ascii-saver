"""Effect Library view construction (separate from preview lifecycle)."""
from __future__ import annotations
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib
from window_shortcuts import install_close_shortcuts
import ctl
from effect_catalog import EFFECTS
from effect_metadata import effect_caption
from animated_preview import AnimatedPreview
from palette_engine import palette_color_for_round
from helpers import load_config
from adwaita_ui import make_group, adaptive_append_action, adaptive_action_row, append_action, action_row, center_string_dropdown

class GalleryViewMixin:
    def _make_gallery_cards(self):
        general = self._page_boxes["general"]
        appearance = self._page_boxes["appearance"]
        displays = self._page_boxes["displays"]
        animations = self._page_boxes["animations"]
        preview_page = self._page_boxes["preview"]
        self.effect_switches = {}
        self._effect_preview_generation = 0
        self._effect_preview_terminal = None
        self._effect_preview_cancellable = None
        self._effect_preview_pid = None
        self._effect_preview_window = None
        # FlowBox naturally uses 1, 2 or 3 columns depending on available
        # width. Gtk.Grid's fixed three columns made the library unusable when
        # narrowed, even though Preferences itself had adaptive navigation.
        effect_grid = Gtk.FlowBox()
        effect_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        effect_grid.set_min_children_per_line(1)
        effect_grid.set_max_children_per_line(3)
        effect_grid.set_homogeneous(True)
        effect_grid.set_column_spacing(14)
        effect_grid.set_row_spacing(12)
        effect_grid.set_hexpand(True)
        effect_grid.set_valign(Gtk.Align.START)
        self.library_grid = effect_grid
        self.effect_cells = {}
        self.effect_previews = {}

        # Use the original ttfx animated demonstrations for every card. These
        # are representative examples using the upstream sample artwork, not
        # a live rendering of the user's custom logo.
        animations = ctl.data_dir / "effects"
        # Initially load saved colors before widget values have been populated.
        # Once Preferences finishes loading, unsaved edits refresh the cards.
        palette_config = load_config(ctl.config_file)
        thumbnail_color = palette_color_for_round(palette_config, None, 0)
        thumbnail_background = palette_config.get('background', '#000000')
        for pos, name in enumerate(EFFECTS):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
            card.add_css_class("effect-library-card")
            card.set_size_request(205, 166)
            card.set_hexpand(True)
            # Thumbnail and checkbox are two ways to toggle the same state.
            # Play remains separate and must never change inclusion.
            check = Gtk.CheckButton(label=name)
            check.set_hexpand(True)
            check.set_tooltip_text(f"Include {name} in random animations")
            thumbnail_button = Gtk.Button()
            thumbnail_button.add_css_class("flat")
            thumbnail_button.set_hexpand(True)
            thumbnail_button.set_tooltip_text(f"Toggle {name} in the enabled effects")
            thumbnail_button.connect("clicked", self._toggle_gallery_thumbnail, check)
            animation_path = animations / f"{name}.aspr"
            if animation_path.is_file():
                try:
                    image = AnimatedPreview(
                        animation_path, foreground=thumbnail_color,
                        background=thumbnail_background)
                    image.set_tooltip_text(
                        f"Animated {name} example, tinted with the first selected palette color")
                    thumbnail_button.set_child(image)
                    self.effect_previews[name] = image
                except (GLib.Error, OSError, ValueError) as error:
                    thumbnail_button.set_child(Gtk.Label(label=f"Preview error: {error}", wrap=True))
            else:
                fallback = Gtk.Label(label="Preview unavailable")
                fallback.add_css_class("dim-label")
                fallback.set_size_request(196, 112)
                thumbnail_button.set_child(fallback)
            card.append(thumbnail_button)
            actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            actions.append(check)
            button = Gtk.Button.new_from_icon_name("media-playback-start-symbolic")
            button.set_tooltip_text(f"Preview {name} with your own artwork")
            button.connect("clicked", self._preview_effect, name)
            actions.append(button)
            card.append(actions)
            # Show the same suggested classifications used by the filters.
            # These are not measured times or per-device performance results.
            classification = Gtk.Label(label=effect_caption(name), xalign=0)
            classification.add_css_class("dim-label")
            classification.set_tooltip_text("Suggested duration and intensity, not measured")
            card.append(classification)
            effect_grid.insert(card, -1)
            self.effect_switches[name] = check
            self.effect_cells[name] = card
    def _toggle_gallery_thumbnail(self, _button, check):
        check.set_active(not check.get_active())

    def _make_gallery_window(self):
        general = self._page_boxes["general"]
        appearance = self._page_boxes["appearance"]
        displays = self._page_boxes["displays"]
        animations = self._page_boxes["animations"]
        preview_page = self._page_boxes["preview"]
        effect_grid = self.library_grid
        style = Gtk.CssProvider()
        style.load_from_data(b"""
        .effect-library-card {
            background: alpha(@theme_fg_color, 0.055);
            border: 1px solid alpha(@theme_fg_color, 0.14);
            border-radius: 12px;
            padding: 12px;
        }
        .effect-library-card:hover { border-color: alpha(@theme_selected_bg_color, 0.55); }
        .unsaved-banner { background-color: @window_bg_color; border: 1px solid @borders;
                          border-radius: 12px; padding: 10px 14px; box-shadow: 0 5px 16px alpha(black, 0.20); }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # Header controls are OUTSIDE the gallery scroller. Only the effect
        # cards scroll, so a huge grid cannot push the actual viewport down to
        # a tiny strip. The scrolling pane always receives the spare height.
        effect_grid.set_margin_top(10)
        effect_grid.set_margin_bottom(10)
        effect_grid.set_margin_start(10)
        effect_grid.set_margin_end(10)
        gallery_header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        gallery_header.set_margin_top(12)
        gallery_header.set_margin_bottom(4)
        gallery_header.set_margin_start(14)
        gallery_header.set_margin_end(14)
        gallery_header.append(Gtk.Label(label="Enabled animations", xalign=0, css_classes=["heading"]))
        library_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.library_search = Gtk.SearchEntry(hexpand=True)
        self.library_search.set_placeholder_text("Search 37 effects")
        self.library_search.set_tooltip_text("Filter effects by name without changing which effects are enabled")
        self.library_search.connect("search-changed", self._filter_effect_library)
        library_toolbar.append(self.library_search)
        self.library_duration = Gtk.DropDown.new_from_strings(["All durations", "Short", "Medium", "Long"])
        self.library_duration.set_tooltip_text("Suggested durations, not measured on your computer")
        self.library_duration.connect("notify::selected", self._filter_effect_library)
        library_toolbar.append(self.library_duration)
        self.library_intensity = Gtk.DropDown.new_from_strings(["All intensities", "Gentle", "Moderate", "Energetic"])
        self.library_intensity.set_tooltip_text("Qualitative intensity classification")
        self.library_intensity.connect("notify::selected", self._filter_effect_library)
        for dropdown in (self.library_duration, self.library_intensity):
            center_string_dropdown(dropdown)
        library_toolbar.append(self.library_intensity)
        gallery_header.append(library_toolbar)
        self.library_count = Gtk.Label(xalign=0)
        self.library_count.add_css_class("dim-label")
        gallery_header.append(self.library_count)
        preview_mode_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        preview_mode_row.append(Gtk.Label(label="Play preview:", xalign=0))
        self.library_preview_mode = Gtk.DropDown.new_from_strings([
            "Large separate window", "Pinned below effect cards",
        ])
        self.library_preview_mode.set_tooltip_text(
            "Separate: freely resizable, stays open on input. "
            "Pinned: compact preview remains visible while you scroll.")
        self.library_preview_mode.connect("notify::selected", self._preview_mode_changed_from_library)
        self.effect_preview_mode.connect("notify::selected", self._preview_mode_changed_from_settings)
        preview_mode_row.append(self.library_preview_mode)
        self._last_preview_effect = None
        self.replay_preview_button = Gtk.Button(label="Replay last effect")
        self.replay_preview_button.set_sensitive(False)
        self.replay_preview_button.set_tooltip_text(
            "Open the last played effect again, including after closing the pinned preview")
        self.replay_preview_button.connect("clicked", self._reopen_effect_preview)
        preview_mode_row.append(self.replay_preview_button)
        gallery_header.append(preview_mode_row)
        self._filter_effect_library()

        self.preview_title = Gtk.Label(label="Select Play on an effect to preview it", xalign=0, hexpand=True)
        self.preview_title.add_css_class("dim-label")
        preview_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        preview_controls.append(self.preview_title)
        stop_preview = Gtk.Button(label="Close preview")
        stop_preview.connect("clicked", self._stop_effect_preview)
        preview_controls.append(stop_preview)
        # ScrolledWindow prevents VTE's terminal's natural height from taking
        # over the gallery. It is deliberately bounded to 180 logical pixels.
        self.preview_area = Gtk.ScrolledWindow()
        self.preview_area.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.preview_area.set_min_content_height(240)
        self.preview_area.set_max_content_height(280)
        self.preview_area.set_propagate_natural_height(False)
        self.preview_area.set_vexpand(False)
        self.preview_area.set_valign(Gtk.Align.CENTER)
        self.preview_area.set_halign(Gtk.Align.CENTER)
        self.preview_area.set_hexpand(True)
        self.live_preview = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for setter in (self.live_preview.set_margin_start, self.live_preview.set_margin_end,
                       self.live_preview.set_margin_top, self.live_preview.set_margin_bottom):
            setter(10)
        self.live_preview.append(preview_controls)
        self.live_preview.append(self.preview_area)
        self.live_preview_revealer = Gtk.Revealer()
        self.live_preview_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.live_preview_revealer.set_child(self.live_preview)
        self.live_preview_revealer.set_vexpand(False)

        # Keep the tool window transient to Preferences, so opening the library
        # does not occupy the application's primary task-manager position.
        self.gallery_window = Adw.Window(
            transient_for=self, title="ASCII Saver · Effect library")
        self.gallery_window.set_default_size(1000, 860)
        install_close_shortcuts(self.gallery_window, Gtk, Gdk)
        gallery_scroll = Gtk.ScrolledWindow()
        gallery_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        gallery_scroll.set_vexpand(True)
        gallery_scroll.set_hexpand(True)
        gallery_scroll.set_min_content_height(320)
        gallery_scroll.set_child(effect_grid)
        self.gallery_scroll = gallery_scroll
        gallery_scroll.get_vadjustment().connect("value-changed", self._sync_gallery_previews)
        gallery_scroll.get_vadjustment().connect("changed", self._queue_gallery_sync)
        gallery_scroll.connect("map", self._queue_gallery_sync)
        gallery_shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        gallery_shell.set_vexpand(True)
        gallery_shell.append(gallery_header)
        # An empty search is a genuine empty state, not a blank gallery that
        # appears to have lost all of its effects. Filter changes never toggle
        # checkboxes or write configuration values.
        self.gallery_stack = Gtk.Stack()
        self.gallery_stack.set_hexpand(True)
        self.gallery_stack.set_vexpand(True)
        self.gallery_stack.add_named(gallery_scroll, "gallery")
        empty_page = Adw.StatusPage()
        empty_page.set_icon_name("edit-find-symbolic")
        empty_page.set_title("No matching effects")
        empty_page.set_description("Try another search or clear the filters. Your enabled effects are unchanged.")
        clear_filters = Gtk.Button(label="Clear filters")
        clear_filters.add_css_class("suggested-action")
        clear_filters.set_halign(Gtk.Align.CENTER)
        clear_filters.connect("clicked", self._clear_library_filters)
        empty_page.set_child(clear_filters)
        self.gallery_stack.add_named(empty_page, "empty")
        gallery_shell.append(self.gallery_stack)
        self._filter_effect_library()
        # Preview appears BELOW the guaranteed-height card viewport and never
        # steals its expansion. Users can still scroll the library while playing.
        gallery_shell.append(self.live_preview_revealer)
        library_toolbar_view = Adw.ToolbarView()
        library_toolbar_view.add_top_bar(Adw.HeaderBar())
        library_toolbar_view.set_content(gallery_shell)
        # Non-shifting, contextual Save/Discard controls belong to the library,
        # not in a different Preferences window hidden behind it.
        self.library_unsaved_banner = Gtk.Revealer()
        self.library_unsaved_banner.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
        library_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        library_actions.add_css_class("unsaved-banner")
        library_actions.append(Gtk.Label(label="Unsaved changes", xalign=0, hexpand=True))
        discard_library = Gtk.Button(label="Discard")
        discard_library.connect("clicked", self._discard_library_changes)
        library_actions.append(discard_library)
        save_library = Gtk.Button(label="Save")
        save_library.add_css_class("suggested-action")
        save_library.connect("clicked", self._save_library_changes)
        library_actions.append(save_library)
        self.library_unsaved_banner.set_child(library_actions)
        self.library_unsaved_banner.set_halign(Gtk.Align.FILL)
        self.library_unsaved_banner.set_valign(Gtk.Align.START)
        self.library_unsaved_banner.set_margin_top(56)
        self.library_unsaved_banner.set_margin_start(12)
        self.library_unsaved_banner.set_margin_end(12)
        library_overlay = Gtk.Overlay()
        library_overlay.set_child(library_toolbar_view)
        library_overlay.add_overlay(self.library_unsaved_banner)
        self.library_toast_overlay = Adw.ToastOverlay()
        self.library_toast_overlay.set_child(library_overlay)
        self.gallery_window.set_content(self.library_toast_overlay)
        # Keep search, filters and preview-mode actions reachable when the
        # library window is narrower than the default 1000 logical pixels.
        compact = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 700sp"))
        compact.add_setter(library_toolbar, "orientation", Gtk.Orientation.VERTICAL)
        compact.add_setter(preview_mode_row, "orientation", Gtk.Orientation.VERTICAL)
        self.gallery_window.add_breakpoint(compact)
        smallest = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 440sp"))
        smallest.add_setter(library_actions, "orientation", Gtk.Orientation.VERTICAL)
        self.gallery_window.add_breakpoint(smallest)
        self.gallery_window.connect("close-request", self._close_gallery)
        self.gallery_window.connect("notify::is-active", self._gallery_activation_changed)
        preview_group = make_group("Library preview")
        adaptive_action_row(preview_group, "Effect preview mode", self.effect_preview_mode)
        preview_page.append(preview_group)
