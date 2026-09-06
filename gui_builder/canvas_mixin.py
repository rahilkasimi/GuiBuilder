"""Canvas interaction, hierarchy, selection and element operations."""
from .dependencies import *
from bisect import bisect_left
from .config import *
from .models import DesignElement


class CanvasMixin:
        @staticmethod
        def _is_text_input_widget(widget) -> bool:
            """Return True when keyboard clipboard/selection shortcuts should be
            handled by Tk's native text-entry bindings instead of the canvas.

            This prevents Ctrl+C / Ctrl+V / Ctrl+A in the property inspector
            (or code editor) from also operating on canvas elements.
            """
            if widget is None:
                return False
            try:
                if widget.winfo_class() in ("Entry", "TEntry", "Text"):
                    return True
            except tk.TclError:
                pass
            return False

        def _refresh_geometry_property_rows(self, elem: DesignElement) -> None:
            """Push the current canvas width/height into the inspector while a
            resize gesture is in progress, without rebuilding the inspector or
            triggering live-edit callbacks."""
            if len(self.selected_elems) != 1 or self.selected_elems[0] is not elem:
                return
            for row in self.prop_rows:
                field_key = row.get("field_key")
                var = row.get("var")
                if field_key == "canvas_w" and var is not None and row.get("visible"):
                    self._set_var_quiet(
                        var, f"{elem.canvas_w:.2f}", row,
                        lambda *args, r=row: self._on_live_prop_change(r)
                    )
                elif field_key == "canvas_h" and var is not None and row.get("visible"):
                    self._set_var_quiet(
                        var, f"{elem.canvas_h:.2f}", row,
                        lambda *args, r=row: self._on_live_prop_change(r)
                    )

        def _elements_in_container(self, container_id: Optional[int]) -> List[DesignElement]:
            """Return visible elements scoped to one container.

            ``None`` means the design root, so only top-level elements are
            returned. A real container id returns all visible descendants
            recursively; nested containers therefore remain fully editable
            from their parent scope.
            """
            visible = self._visible_elements()
            if container_id is None:
                return [e for e in visible if e.parent_id is None]

            result = []
            for elem in visible:
                cur = elem
                seen = set()
                while cur.parent_id is not None and cur.parent_id not in seen:
                    if cur.parent_id == container_id:
                        result.append(elem)
                        break
                    seen.add(cur.parent_id)
                    parent = self._by_id.get(cur.parent_id)
                    if parent is None:
                        break
                    cur = parent
            return result

        def _selection_container_for_point(self, x: float, y: float) -> Optional[DesignElement]:
            """Resolve the innermost container under a point for selection scope."""
            return self._container_at(x, y)

        def _selection_container_for_current_context(self) -> Optional[DesignElement]:
            """Resolve the active selection scope from the current canvas context."""
            active_id = getattr(self, "active_container_id", None)
            if active_id is not None:
                return self._by_id.get(active_id)
            return None

        def _select_elements(self, elements: List[DesignElement], status_prefix: str,
                            mode: str = "replace") -> str:
            """Apply a selection operation without changing group membership.

            ``replace`` selects exactly ``elements``; ``add`` extends the
            current selection; ``toggle`` adds unselected elements and removes
            already-selected elements.  This is intentionally independent of
            the persisted Group property: Shift/Ctrl operate on the current
            selection, while groups remain a separate feature.
            """
            incoming = [e for e in elements if e in self.elements]
            current = list(self.selected_elems)

            if mode == "replace":
                target = incoming
            elif mode == "add":
                target = current[:] 
                for elem in incoming:
                    if elem not in target:
                        target.append(elem)
            elif mode == "toggle":
                target = current[:] 
                for elem in incoming:
                    if elem in target:
                        target.remove(elem)
                    else:
                        target.append(elem)
            else:
                target = incoming

            target_ids = {e.elem_id for e in target}
            for elem in self.selected_elems:
                if elem.elem_id not in target_ids:
                    elem.selected = False
                    self.renderer.redraw_element(elem)
            for elem in target:
                was_selected = elem.selected
                elem.selected = True
                if not was_selected or mode != "replace":
                    self.renderer.redraw_element(elem)

            self.selected_elems[:] = target
            self._reorder_elements()
            if len(self.selected_elems) == 1:
                self._show_properties(self.selected_elems[0])
                self._update_position_status(self.selected_elems[0])
            elif self.selected_elems:
                self._show_properties_multi()
            else:
                self._show_properties(None)
            self._update_status(f"{status_prefix} {len(self.selected_elems)} element(s).")
            return "break"

        @staticmethod
        def _selection_modifiers(event):
            """Return (shift, ctrl) using Tk's portable modifier bit masks."""
            state = getattr(event, "state", 0)
            return bool(state & 0x0001), bool(state & 0x0004)

        def _selection_mode_from_event(self, event):
            """Map canvas modifiers to independent selection semantics.

            Shift = additive selection.
            Ctrl  = toggle selection.
            Ctrl+Shift = toggle selection (Ctrl takes precedence).
            No modifier = normal single selection.
            """
            shift, ctrl = self._selection_modifiers(event)
            if ctrl:
                return "toggle"
            if shift:
                return "add"
            return "replace"

        def _select_all(self, event=None):
            """Legacy Ctrl+A remains a root-level select-all operation.

            Text controls retain native Ctrl+A. Container-scoped selection is
            deliberately provided by Ctrl+Shift+A so existing projects keep
            their established Ctrl+A workflow.
            """
            widget = getattr(event, "widget", None) if event is not None else None
            if widget is not None and self._is_text_input_widget(widget):
                return
            return self._select_elements(
                self._visible_elements(),
                "Selected all visible"
            )

        def _select_all_scoped(self, event=None):
            """Select only the elements inside the active container."""
            widget = getattr(event, "widget", None) if event is not None else None
            if widget is not None and self._is_text_input_widget(widget):
                return
            container = self._selection_container_for_current_context()
            scoped = self._elements_in_container(container.elem_id if container else None)
            if container is None:
                return self._select_elements(scoped, "Selected all root-level")
            return self._select_elements(
                scoped,
                f"Selected all elements in {container.elem_type} ID {container.elem_id}"
            )

        def _rebuild_index(self):
            """Rebuild the id->element and parent_id->children lookup tables.
            Call this once after any code that adds/removes/replaces entries in
            self.elements. It's O(n), which is far cheaper than the O(n) linear
            scans it replaces when those scans happen inside a per-element loop.
            """
            self._by_id = {e.elem_id: e for e in self.elements}
            children: Dict[int, List[DesignElement]] = {}
            for e in self.elements:
                if e.parent_id is not None:
                    children.setdefault(e.parent_id, []).append(e)
            self._children_by_parent = children

        def _move_with_keys(self, event):
            if not self.selected_elems:
                return
            if event.widget.winfo_class() in ("Entry", "TEntry", "Text"):
                return

            dx, dy = 0, 0
            if event.keysym == "Up":
                dy = -1
            elif event.keysym == "Down":
                dy = 1
            elif event.keysym == "Left":
                dx = -1
            elif event.keysym == "Right":
                dx = 1

            step = GRID_SIZE if (event.state & 0x0001) else 1
            dx *= step
            dy *= step

            for elem in self.selected_elems:
                elem.x = max(0, min(elem.x + dx, self.CANVAS_W - elem.canvas_w))
                elem.y = max(0, min(elem.y + dy, self.CANVAS_H - elem.canvas_h))
                self.renderer.redraw_element(elem)

            self._update_code_for_moved_elements()
            self._update_code()
            self._update_position_status(self.selected_elems[0] if len(self.selected_elems)==1 else None)

            self._schedule_save()

        def _update_code_for_moved_elements(self):
            # Used to patch each moved element individually via
            # PropertiesMixin._update_code_for_element. That per-element
            # granularity doesn't buy anything anymore -- regenerating the
            # whole designer module is already safe and cheap regardless
            # of how many elements moved, so every caller of this just
            # gets a single full regen now.
            self._regenerate_designer_code()

        def _is_element_visible(self, elem: DesignElement) -> bool:
            current = elem
            seen = set()
            while current.parent_id is not None:
                parent = self._by_id.get(current.parent_id)
                if parent is None:
                    break
                if parent.elem_type == "Notebook":
                    child = current
                    tab = child.parent_tab
                    if tab is None:
                        tab = 0
                    active = int(parent.props.get("active_tab", 0) or 0)
                    if tab != active:
                        return False
                current = parent
                if current.elem_id in seen:
                    break
                seen.add(current.elem_id)
            return True

        def _compute_depths(self) -> Dict[int, int]:
            """Nesting depth (0 = top-level) for every element, via the parent
            index. Used both to set canvas z-order (deeper = raised later = on
            top) and to hit-test clicks in that same order, so a click always
            resolves to the innermost/topmost thing under the cursor -- not to
            whichever element happens to sit earlier in self.elements. An
            element's position in self.elements reflects when it was created,
            not its current nesting, so list order and stacking order can and
            do diverge (e.g. an element created before a container that's
            later dragged inside it).
            """
            depths: Dict[int, int] = {}

            def depth_of(e: DesignElement, visiting: set) -> int:
                if e.elem_id in depths:
                    return depths[e.elem_id]
                if e.parent_id is None or e.elem_id in visiting:
                    depths[e.elem_id] = 0
                    return 0
                parent = self._by_id.get(e.parent_id)
                if parent is None:
                    depths[e.elem_id] = 0
                    return 0
                visiting.add(e.elem_id)
                d = depth_of(parent, visiting) + 1
                visiting.discard(e.elem_id)
                depths[e.elem_id] = d
                return d

            for e in self.elements:
                depth_of(e, set())
            return depths

        def _visible_elements(self) -> List[DesignElement]:
            return [e for e in self.elements if self._is_element_visible(e)]

        def _draw_canvas_handles(self):
            """Draw subtle resize handles on the logical canvas boundary when no element is selected."""
            for item in self.canvas_handle_ids.values():
                try: self.canvas.delete(item)
                except tk.TclError: pass
            self.canvas_handle_ids = {}
            if self.selected_elems: return
            z=self._zoom or 1.0; x=0; y=0; w=self.CANVAS_W*z; h=self.CANVAS_H*z
            pts={"NW":(x,y),"N":(x+w/2,y),"NE":(x+w,y),"E":(x+w,y+h/2),"SE":(x+w,y+h),"S":(x+w/2,y+h),"SW":(x,y+h),"W":(x,y+h/2)}
            for name,(hx,hy) in pts.items():
                r=4
                self.canvas_handle_ids[name]=self.canvas.create_rectangle(hx-r,hy-r,hx+r,hy+r,fill="#FFFFFF",outline="#607D8B",width=1,tags=("canvas_handle",))
            self.canvas.tag_raise("canvas_handle")

        def _canvas_handle_at(self, x, y):
            if self.selected_elems: return None
            z=self._zoom or 1.0; pts={"NW":(0,0),"N":(self.CANVAS_W/2,0),"NE":(self.CANVAS_W,0),"E":(self.CANVAS_W,self.CANVAS_H/2),"SE":(self.CANVAS_W,self.CANVAS_H),"S":(self.CANVAS_W/2,self.CANVAS_H),"SW":(0,self.CANVAS_H),"W":(0,self.CANVAS_H/2)}
            radius=10/max(z,0.01)
            for name,(hx,hy) in pts.items():
                if abs(x-hx)<=radius and abs(y-hy)<=radius: return name
            return None

        def _canvas_resize_preview(self, handle, dx, dy):
            ox,oy=self.canvas_resize_orig
            nw,nh=ox,oy
            min_w,min_h=120,80
            if "E" in handle: nw=ox+dx
            if "S" in handle: nh=oy+dy
            if "W" in handle: nw=ox-dx
            if "N" in handle: nh=oy-dy
            self.CANVAS_W=round(max(min_w,nw),2); self.CANVAS_H=round(max(min_h,nh),2)
            self._resnap_status_bars()
            self.canvas.config(scrollregion=(0,0,int(self.CANVAS_W*self._zoom),int(self.CANVAS_H*self._zoom)))
            self.renderer.draw_canvas_surface(self.CANVAS_W,self.CANVAS_H,self.CANVAS_BG)
            self.renderer.draw_canvas_background(self.CANVAS_BG_IMAGE,self.CANVAS_BG_IMAGE_MODE,self.CANVAS_BG_IMAGE_ANCHOR,self.CANVAS_W,self.CANVAS_H)
            self.renderer.draw_canvas_border(self.CANVAS_W,self.CANVAS_H)
            self._redraw_all_elements()
            self._draw_canvas_handles()
            self._show_canvas_properties()

        def _redraw_all_elements(self):
            for e in self.elements:
                self.renderer.erase_element(e)
            for e in self._visible_elements():
                self.renderer.draw_element(e)
            self._reorder_elements()
            self._draw_canvas_handles()

        def _reorder_elements(self):
            visible = self._visible_elements()
            depths = self._compute_depths()
            order_index = {e.elem_id: i for i, e in enumerate(self.elements)}
            sorted_elems = sorted(
                visible,
                key=lambda e: (depths.get(e.elem_id, 0), order_index.get(e.elem_id, 0))
            )
            for e in sorted_elems:
                self.canvas.tag_raise(f"elem_{e.elem_id}")
            self.canvas.tag_raise("canvas_border")
            self.canvas.tag_raise("handle")

        def _tool_selected(self, tool_name: str):
            self.pending_type = tool_name
            self._highlight_active_tool(tool_name)
            self._update_status(
                f"{ELEMENT_TYPES[tool_name]['display']} selected — click canvas to place it."
                )

        def _notebook_tab_at(self, elem: DesignElement, x: float, y: float) -> Optional[int]:
            if elem.elem_type != "Notebook":
                return None
            if not (elem.x <= x <= elem.x + elem.canvas_w and elem.y <= y <= elem.y + 26):
                return None
            tabs = elem.props.get("tabs", ["Tab 1", "Tab 2"]) or ["Tab 1"]
            tab_width = max(58, min(120, int(
                (elem.canvas_w - 10) / max(1, min(len(tabs), 4))
                )
                                      )
                             )
            tab_x = elem.x + 5
            for i, _ in enumerate(tabs):
                tw = min(tab_width, elem.x + elem.canvas_w - 4 - tab_x)
                if tab_x <= x <= tab_x + tw:
                    return i
                tab_x += tw + 3
                if tab_x >= elem.x + elem.canvas_w:
                    break
            return None

        def _container_at(self, x: float, y: float) -> Optional[DesignElement]:
            containers = []
            for elem in self._visible_elements():
                if elem.elem_type not in CONTAINER_TYPES:
                    continue
                if elem.elem_type == "Notebook":
                    if not (elem.x <= x <= elem.x + elem.canvas_w and elem.y + 26 <= y <= elem.y + elem.canvas_h):
                        continue
                elif not elem.contains_point(x, y):
                    continue
                area = max(1, elem.canvas_w * elem.canvas_h)
                depth = 0
                cur = elem
                seen = set()
                while cur.parent_id is not None and cur.parent_id not in seen:
                    seen.add(cur.parent_id)
                    p = self._by_id.get(cur.parent_id)
                    if not p:
                        break
                    depth += 1
                    cur = p
                containers.append((depth, -area, elem))
            if not containers:
                return None
            containers.sort(key=lambda t: (t[0], t[1]), reverse=True)
            return containers[0][2]

        def _set_notebook_active_tab(
                self, notebook: DesignElement, tab_index: int
                ):
            tabs = notebook.props.get("tabs", ["Tab 1", "Tab 2"]) or ["Tab 1"]
            if 0 <= tab_index < len(tabs):
                notebook.props["active_tab"] = tab_index
                for e in self.elements:
                    e.selected = False
                self.selected_elems.clear()
                notebook.selected = True
                self.selected_elems.append(notebook)
                self._redraw_all_elements()
                self._show_properties(notebook)
                self._update_code()
                self._save_state()
                self._update_status(
                    f"Notebook ID {notebook.elem_id}: {tabs[tab_index]} selected."
                    )

        def _logical_xy(self, event):
            z = self._zoom or 1.0
            return self.canvas.canvasx(event.x) / z, self.canvas.canvasy(event.y) / z

        def _update_resize_cursor(self, x, y):
            """Swap the canvas mouse cursor to match whichever resize
            handle (element or whole-canvas) is under the pointer at
            logical coordinates (x, y) -- a diagonal cursor over a
            corner handle, a horizontal/vertical one over an edge
            handle, the default arrow everywhere else. Only takes effect
            while nothing is actively being dragged, so it doesn't fight
            with the drag itself once a resize/move is underway.
            """
            if self.drag_mode not in ("none", None):
                return
            for elem in self.selected_elems:
                hit = elem.hit_handle(x, y)
                if hit and hit != "DEL":
                    cursor = HANDLE_CURSOR_MAP.get(hit, "")
                    if str(self.canvas.cget("cursor")) != cursor:
                        self.canvas.config(cursor=cursor)
                    return
            canvas_handle = self._canvas_handle_at(x, y)
            if canvas_handle:
                cursor = HANDLE_CURSOR_MAP.get(canvas_handle, "")
                if str(self.canvas.cget("cursor")) != cursor:
                    self.canvas.config(cursor=cursor)
                return
            if str(self.canvas.cget("cursor")) != "":
                self.canvas.config(cursor="")

        def _tag_drag_group(self):
            """Tag every canvas item belonging to the currently selected
            elements (plus any children cascaded along with a container) with
            a shared "dragging" tag, so _on_canvas_drag can move the whole
            group with a single canvas.move() call per mouse-move event
            instead of one call per element. Rebuilt fresh at the start of
            every move-drag.
            """
            self.canvas.dtag("dragging", "dragging")
            group_ids: set = set()

            def collect(e: DesignElement):
                if e.elem_id in group_ids:
                    return
                group_ids.add(e.elem_id)
                if e.elem_type in CONTAINER_TYPES:
                    for child in self._children_by_parent.get(e.elem_id, []):
                        collect(child)

            for e in self.selected_elems:
                collect(e)

            for eid in group_ids:
                self.canvas.addtag_withtag("dragging", f"elem_{eid}")
                el = self._by_id.get(eid)
                if el:
                    for hid in el.handle_ids.values():
                        self.canvas.addtag_withtag("dragging", hid)

        def _on_canvas_click(self, event):
            x, y = self._logical_xy(event)
            z = self._zoom or 1.0
            selection_mode = self._selection_mode_from_event(event)
            context_container = self._selection_container_for_point(x, y)
            self.active_container_id = context_container.elem_id if context_container else None

            canvas_handle = self._canvas_handle_at(x, y)
            if canvas_handle:
                self.drag_mode = "canvas_resize"
                self.active_handle = canvas_handle
                self.mouse_down_pos = (x, y)
                self.canvas_resize_orig = (self.CANVAS_W, self.CANVAS_H)
                return

            if self.pending_type:
                tool = self.pending_type
                self.pending_type = None
                self._reset_tool_colors()
                self._add_element(tool, x, y)
                return

            self.elem_origs = {e.elem_id: (e.x, e.y, e.canvas_w, e.canvas_h) for e in self.elements}

            # Same depth-ordered (topmost-first) iteration as _find_element_at,
            # for the same reason: list order isn't stacking order once an
            # element has been reparented into a container after creation.
            depths = self._compute_depths()
            ordered_candidates = sorted(self._visible_elements(),
                                         key=lambda e: depths.get(e.elem_id, 0)
                                         )
            for candidate in reversed(ordered_candidates):
                tab_index = self._notebook_tab_at(candidate, x, y)
                if tab_index is not None:
                    self._set_notebook_active_tab(candidate, tab_index)
                    self._reset_drag_state()
                    return

            handle_hit = None
            for elem in self.selected_elems:
                hit = elem.hit_handle(x, y)
                if hit:
                    handle_hit = hit
                    self.drag_mode = "resize"
                    self.drag_elem = elem
                    self.mouse_down_pos = (x, y)
                    self.active_handle = hit
                    self.pending_type = None
                    self._reset_tool_colors()
                    break

            if handle_hit:
                if handle_hit == "DEL":
                    self._delete_selected()
                    return
                return

            clicked = self._find_element_at(x, y)
            if clicked:
                # A plain click on an already-selected item keeps the current
                # multi-selection intact so the entire selection can be moved.
                # Shift adds only the clicked element. Ctrl toggles only the
                # clicked element. Neither modifier expands a persisted group.
                already_in_group = (clicked in self.selected_elems
                                    and len(self.selected_elems) > 1
                                    and selection_mode == "replace")
                if not already_in_group:
                    if selection_mode == "replace":
                        group_members = self._group_members(clicked)
                        chosen = group_members if len(group_members) > 1 else [clicked]
                        status = "Selected group" if len(group_members) > 1 else "Selected"
                    else:
                        chosen = [clicked]
                        status = "Added to selection" if selection_mode == "add" else "Toggled selection"
                    self._select_elements(chosen, status, mode=selection_mode)

                    # Ctrl-click removes an item from the selection.  That is a
                    # selection-only gesture, not the beginning of a move.
                    if selection_mode == "toggle" and clicked not in self.selected_elems:
                        self._reset_drag_state()
                        return

                self.drag_mode = "move"
                self.drag_elem = clicked
                self.mouse_down_pos = (x, y)
                self.active_handle = None
                self._last_move_delta = (0, 0)
                self._prepare_alignment_guides()
                self._tag_drag_group()
            else:
                # Defer selection changes until marquee release. This allows
                # Shift/Ctrl to define the marquee operation without repeatedly
                # rebuilding the inspector while the mouse is pressed.
                self._selection_drag_mode = selection_mode
                self._reset_drag_state(keep_selection_drag=True)
                self.drag_mode = "select_box"
                # Preserve the established left-button behavior: the normal
                # marquee selects across the whole visible canvas. Scoped
                # marquee selection is intentionally a separate right-button
                # interaction.
                self.selection_scope_id = None
                self.mouse_down_pos = (x, y)
                self.selection_box_id = self.canvas.create_rectangle(x * z, y * z,
                                                                      x * z, y * z,
                                                                      dash=(4, 4),
                                                                      outline="#1976D2"
                                                                      )

            self.canvas.focus_set()

        def _on_canvas_scoped_select_press(self, event):
            """Start a right-button selection rectangle scoped to the active container."""
            x, y = self._logical_xy(event)
            z = self._zoom or 1.0
            context_container = self._selection_container_for_point(x, y)
            self.active_container_id = context_container.elem_id if context_container else None
            self.selection_scope_id = self.active_container_id
            self.mouse_down_pos = (x, y)
            self.drag_mode = "select_box_scoped"
            self.selection_box_id = self.canvas.create_rectangle(
                x * z, y * z, x * z, y * z,
                dash=(4, 4), outline="#7B1FA2"
            )
            return "break"

        def _on_canvas_scoped_select_drag(self, event):
            if self.drag_mode != "select_box_scoped" or not self.mouse_down_pos:
                return "break"
            x, y = self._logical_xy(event)
            z = self._zoom or 1.0
            self.canvas.coords(
                self.selection_box_id,
                self.mouse_down_pos[0] * z, self.mouse_down_pos[1] * z,
                x * z, y * z
            )
            return "break"

        def _on_canvas_scoped_select_release(self, event):
            if self.drag_mode != "select_box_scoped" or not self.mouse_down_pos:
                return "break"
            mx, my = self._logical_xy(event)
            if self.mouse_down_pos and abs(mx - self.mouse_down_pos[0]) <= 3 and abs(my - self.mouse_down_pos[1]) <= 3:
                if self.selection_box_id:
                    self.canvas.delete(self.selection_box_id)
                    self.selection_box_id = None
                self._reset_drag_state()
                return self._show_canvas_context_menu(event)
            x1, y1 = min(self.mouse_down_pos[0], mx), min(self.mouse_down_pos[1], my)
            x2, y2 = max(self.mouse_down_pos[0], mx), max(self.mouse_down_pos[1], my)
            scoped = self._elements_in_container(self.selection_scope_id)
            matches = []
            for elem in scoped:
                cx = elem.x + elem.canvas_w / 2
                cy = elem.y + elem.canvas_h / 2
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    matches.append(elem)
            self._select_elements(matches, "Scoped selection")
            if self.selection_box_id:
                self.canvas.delete(self.selection_box_id)
                self.selection_box_id = None
            self._reset_drag_state()
            return "break"

        def _find_element_at(self, x: int, y: int) -> Optional[DesignElement]:
            # Hit-test in actual rendered stacking order (deepest/topmost
            # first) -- the same order _reorder_elements() uses to raise
            # canvas items -- not self.elements list order. An element created
            # before a container it's later dragged into keeps its earlier
            # position in self.elements even though it now renders on top of
            # that container; hit-testing by list order would make it match
            # the container first and become permanently unclickable.
            depths = self._compute_depths()
            ordered = sorted(self._visible_elements(),
                              key=lambda e: depths.get(e.elem_id, 0)
                              )
            for elem in reversed(ordered):
                if elem.contains_point(x, y):
                    return elem
            return None

        def _on_canvas_drag(self, event):
            if not self.mouse_down_pos:
                return
            z = self._zoom or 1.0
            mx, my = self._logical_xy(event)
            cum_dx, cum_dy = mx - self.mouse_down_pos[0], my - self.mouse_down_pos[1]

            if self.drag_mode == "canvas_resize":
                self._canvas_resize_preview(self.active_handle, cum_dx, cum_dy)
                return

            if self.drag_mode == "move":
                # Snap once, using the element the user actually grabbed as the
                # anchor, then apply that exact same delta to every selected
                # element (and cascaded container children). Snapping each
                # element to the grid independently -- the old behavior --
                # could round each one onto a different grid line and change
                # the gaps between them during a multi-select drag; a single
                # shared delta keeps relative spacing exact.
                anchor = (self.drag_elem
                          if self.drag_elem and self.drag_elem.elem_id in self.elem_origs
                          else next((e for e in self.selected_elems
                                     if e.elem_id in self.elem_origs), None)
                          )
                if anchor is None:
                    return
                aox, aoy, _, _ = self.elem_origs[anchor.elem_id]
                snapped_x, snapped_y = self.renderer.snap_to_grid(aox + cum_dx,
                                                                   aoy + cum_dy)
                dx, dy = snapped_x - aox, snapped_y - aoy
                dx, snap_x_guide = self._alignment_snap_delta(dx, axis="x")
                dy, snap_y_guide = self._alignment_snap_delta(dy, axis="y")
                self._update_alignment_guides(snap_x_guide, snap_y_guide)

                # Incremental delta since the previous drag frame. Canvas items
                # are translated by this amount, not by the full cumulative
                # delta, since they're already sitting at last frame's position.
                prev_dx, prev_dy = self._last_move_delta
                inc_dx, inc_dy = dx - prev_dx, dy - prev_dy
                self._last_move_delta = (dx, dy)

                moved_ids = set()
                # Elements whose canvas-edge clamp made their actual movement
                # this frame differ from the rest of the group (only possible
                # right at the edge of the canvas) -- corrected individually
                # after the single batched move below.
                clamped: List[Tuple[DesignElement, int, int]] = []

                # Clamp the *whole selection's* combined bounding box against
                # the canvas edges once, instead of clamping each selected
                # element separately against its own bounding box. Elements
                # differ in size and position, so an independent per-element
                # clamp lets one of them hit the edge (and get capped) a
                # frame before another -- their positions relative to each
                # other visibly drift apart or compress the moment any part
                # of the selection reaches a canvas border. A single delta
                # derived from the group's outer extent keeps every selected
                # element's offset from the rest of the group exactly fixed,
                # no matter where the drag ends up being clamped; any element
                # whose own edge coincides with the group's outer edge is
                # still guaranteed to land on-canvas as a result (see the
                # apply_delta docstring below for the short proof).
                top_level_selected = [
                    e for e in self.selected_elems if e.elem_id in self.elem_origs
                ]
                if top_level_selected:
                    min_x = min(self.elem_origs[e.elem_id][0] for e in top_level_selected)
                    min_y = min(self.elem_origs[e.elem_id][1] for e in top_level_selected)
                    max_x = max(self.elem_origs[e.elem_id][0] + self.elem_origs[e.elem_id][2]
                                 for e in top_level_selected)
                    max_y = max(self.elem_origs[e.elem_id][1] + self.elem_origs[e.elem_id][3]
                                 for e in top_level_selected)
                    group_dx = max(-min_x, min(dx, self.CANVAS_W - max_x))
                    group_dy = max(-min_y, min(dy, self.CANVAS_H - max_y))
                else:
                    group_dx, group_dy = dx, dy

                def apply_delta(elem: DesignElement, base_x: int, base_y: int):
                    # No per-element min/max clamp here on purpose: group_dx/
                    # group_dy is already clamped so the *group's* bounding
                    # box [min_x, max_x] x [min_y, max_y] stays within
                    # [0, CANVAS_W] x [0, CANVAS_H] -- and every selected
                    # element's own box is a subset of that group box (by
                    # definition of min_x/max_x/min_y/max_y above), so
                    # base_x/base_y + group_dx/group_dy is guaranteed to
                    # land within canvas bounds too, for every element, with
                    # no further clamping needed.
                    prev_x, prev_y = elem.x, elem.y
                    new_x, new_y = base_x + group_dx, base_y + group_dy
                    if (new_x - prev_x, new_y - prev_y) != (inc_dx, inc_dy):
                        clamped.append((elem, prev_x, prev_y))
                    elem.x, elem.y = new_x, new_y
                    moved_ids.add(elem.elem_id)

                def cascade_move(container: DesignElement, actual_dx: int, actual_dy: int):
                    # A container's children (and, recursively, any of
                    # their own children) must follow the container by
                    # exactly the delta the container itself actually
                    # moved by *after* its own canvas-edge clamp -- never
                    # independently re-clamped against the full canvas
                    # using each child's own bounding box. Children are
                    # always nested within their container's bounds, so
                    # applying the container's already-clamped delta as-is
                    # keeps every descendant on-canvas automatically; the
                    # moment a child gets its own separate min/max clamp
                    # instead, its position relative to the container
                    # silently drifts as soon as the container is dragged
                    # to (or shaken against) a canvas edge.
                    for child in self._children_by_parent.get(
                            container.elem_id, []
                    ):
                        if child.elem_id in moved_ids:
                            continue
                        cox, coy, _, _ = self.elem_origs.get(
                            child.elem_id,
                            (child.x, child.y, child.canvas_w, child.canvas_h)
                            )
                        prev_cx, prev_cy = child.x, child.y
                        new_cx, new_cy = cox + actual_dx, coy + actual_dy
                        if (new_cx - prev_cx, new_cy - prev_cy) != (inc_dx, inc_dy):
                            clamped.append((child, prev_cx, prev_cy))
                        child.x, child.y = new_cx, new_cy
                        moved_ids.add(child.elem_id)
                        if child.elem_type in CONTAINER_TYPES:
                            cascade_move(child, actual_dx, actual_dy)

                for elem in self.selected_elems:
                    if elem.elem_id in moved_ids or elem.elem_id not in self.elem_origs:
                        continue
                    ox, oy, _, _ = self.elem_origs[elem.elem_id]
                    apply_delta(elem, ox, oy)

                    if elem.elem_type in CONTAINER_TYPES:
                        actual_dx, actual_dy = elem.x - ox, elem.y - oy
                        cascade_move(elem, actual_dx, actual_dy)

                # One canvas call moves everything tagged "dragging" this
                # session (set up in _tag_drag_group), instead of a separate
                # canvas.move() per element -- this is what keeps a large
                # multi-selection from feeling laggy while dragging.
                z = getattr(self.renderer, "zoom", 1.0)
                if inc_dx or inc_dy:
                    self.canvas.move("dragging", inc_dx * z, inc_dy * z)
                for elem, prev_x, prev_y in clamped:
                    self.renderer.move_element(elem, elem.x - prev_x - inc_dx,
                                                elem.y - prev_y - inc_dy)

            elif self.drag_mode == "resize":
                for elem in self.selected_elems:
                    if elem.elem_id in self.elem_origs:
                        ox, oy, ow, oh = self.elem_origs[elem.elem_id]
                        nx, ny, nw, nh = self._compute_resize(self.active_handle,
                                                               ox, oy, ow, oh,
                                                               cum_dx, cum_dy
                                                               )
                        elem.x = nx
                        elem.y = ny
                        elem.canvas_w = round(float(nw), 2)
                        elem.canvas_h = round(float(nh), 2)
                        self.renderer.redraw_element(elem)
                        self._refresh_geometry_property_rows(elem)

            elif self.drag_mode == "select_box" and self.selection_box_id:
                self.canvas.coords(
                    self.selection_box_id,
                    self.mouse_down_pos[0] * z, self.mouse_down_pos[1] * z, mx * z,
                    my * z
                )

        def _on_canvas_release(self, event):
            parent_changed = False
            if self.drag_mode == "select_box":
                mx, my = self._logical_xy(event)
                x1, y1 = min(self.mouse_down_pos[0], mx), min(
                    self.mouse_down_pos[1], my
                    )
                x2, y2 = max(self.mouse_down_pos[0], mx), max(
                    self.mouse_down_pos[1], my
                    )
                matches = []
                for elem in self._visible_elements():
                    cx, cy = elem.x + elem.canvas_w / 2, elem.y + elem.canvas_h / 2
                    if x1 <= cx <= x2 and y1 <= cy <= y2:
                        matches.append(elem)
                mode = getattr(self, "_selection_drag_mode", "replace")
                self._select_elements(matches, "Marquee selection", mode=mode)
                if self.selection_box_id:
                    self.canvas.delete(self.selection_box_id)
                    self.selection_box_id = None

            elif self.drag_mode == "canvas_resize":
                self.renderer.draw_canvas_surface(self.CANVAS_W, self.CANVAS_H, self.CANVAS_BG)
                self.renderer.draw_canvas_background(self.CANVAS_BG_IMAGE, self.CANVAS_BG_IMAGE_MODE, self.CANVAS_BG_IMAGE_ANCHOR, self.CANVAS_W, self.CANVAS_H)
                self.renderer.draw_canvas_border(self.CANVAS_W, self.CANVAS_H)
                self._redraw_all_elements()
                self._update_code()
                self._schedule_save()

            elif self.drag_mode in ("move", "resize"):
                if self.drag_mode == "move":
                    for elem in self.selected_elems:
                        if elem.elem_type in CONTAINER_TYPES:
                            continue
                        cx = elem.x + elem.canvas_w / 2
                        cy = elem.y + elem.canvas_h / 2
                        parent = self._container_at(cx, cy)
                        old_parent = elem.parent_id
                        elem.parent_id = parent.elem_id if parent else None
                        if parent and parent.elem_type == "Notebook":
                            elem.parent_tab = int(
                                parent.props.get("active_tab", 0) or 0
                                )
                        elif old_parent != elem.parent_id:
                            elem.parent_tab = None
                        # Track if parent changed
                        if old_parent != elem.parent_id:
                            parent_changed = True

                if parent_changed:
                    # elem.parent_id changed above, but self._children_by_parent
                    # (used by drag-tagging, cascaded container moves, delete
                    # cascade, and notebook tab visibility) is only rebuilt on
                    # add/paste/delete/clear/load -- without this, a
                    # newly-reparented element wouldn't actually behave as part
                    # of its new container (e.g. moving the container wouldn't
                    # carry it along) until some unrelated action happened to
                    # trigger a rebuild.
                    self._rebuild_index()

                self._update_code_for_moved_elements()
                self._update_code()
                self._reorder_elements()
                self._update_position_status(self.selected_elems[0] if len(self.selected_elems)==1 else None)
                self._save_state()

            self._reset_drag_state()

            # If any parent changed, the widget-creation order in the
            # designer module needs to reflect the new nesting -- already
            # covered by the unconditional _regenerate_designer_code()
            # call above, so there's nothing extra to do here now (this
            # used to invalidate + fully regenerate a second time on top
            # of an already-applied per-element patch).

        def _on_canvas_double_click(self, event):
            x, y = self._logical_xy(event)
            elem = self._find_element_at(x, y)
            if elem:
                self._open_code_editor(elem)

        def _compute_resize(self, handle, ox, oy, ow, oh, cum_dx, cum_dy):
            nx, ny, nw, nh = ox, oy, ow, oh
            if "W" in handle:
                nw = max(MIN_W, ow - cum_dx)
                nx = ox + ow - nw
            if "E" in handle:
                nw = max(MIN_W, ow + cum_dx)
            if "N" in handle:
                nh = max(MIN_H, oh - cum_dy)
                ny = oy + oh - nh
            if "S" in handle:
                nh = max(MIN_H, oh + cum_dy)
            nx = max(0, min(nx, self.CANVAS_W - nw))
            ny = max(0, min(ny, self.CANVAS_H - nh))
            nw = min(nw, self.CANVAS_W - nx)
            nh = min(nh, self.CANVAS_H - ny)
            return nx, ny, nw, nh

        def _clear_alignment_guides(self, reset_snap=True):
            for item in getattr(self, "_alignment_guide_ids", []):
                try:
                    self.canvas.delete(item)
                except tk.TclError:
                    pass
            self._alignment_guide_ids = []
            self._alignment_rendered_guides = (None, None)
            if reset_snap:
                self._alignment_snap_state = {"x": None, "y": None}

        def _prepare_alignment_guides(self):
            """Cache candidate alignment axes once at move start."""
            selected_ids = {e.elem_id for e in self.selected_elems}
            xs, ys = set(), set()
            for elem in self._visible_elements():
                if elem.elem_id in selected_ids:
                    continue
                x, y = float(elem.x), float(elem.y)
                w, h = float(elem.canvas_w), float(elem.canvas_h)
                xs.update((x, x + w / 2.0, x + w))
                ys.update((y, y + h / 2.0, y + h))
            self._alignment_guides_x = tuple(sorted(xs))
            self._alignment_guides_y = tuple(sorted(ys))
            self._alignment_moving_bounds = self._moving_bounds()
            self._clear_alignment_guides()

        def _moving_bounds(self):
            moving = [self.elem_origs[e.elem_id] for e in self.selected_elems
                      if e.elem_id in self.elem_origs]
            if not moving:
                return None
            return (min(v[0] for v in moving),
                    min(v[1] for v in moving),
                    max(v[0] + v[2] for v in moving),
                    max(v[1] + v[3] for v in moving))

        def _alignment_snap_delta(self, base_delta, axis="x"):
            """Return an adjusted delta and active guide identity."""
            bounds = getattr(self, "_alignment_moving_bounds", None)
            if not bounds:
                return base_delta, None
            if axis == "x":
                lo, hi = bounds[0], bounds[2]
                current = (lo + base_delta, (lo + hi) / 2.0 + base_delta, hi + base_delta)
                guides = self._alignment_guides_x
            else:
                lo, hi = bounds[1], bounds[3]
                current = (lo + base_delta, (lo + hi) / 2.0 + base_delta, hi + base_delta)
                guides = self._alignment_guides_y

            state_key = axis
            active = self._alignment_snap_state.get(state_key)
            threshold = (self._alignment_release_threshold
                         if active is not None else self._alignment_snap_threshold)

            if active is not None:
                guide, idx = active
                diff = guide - current[idx]
                if abs(diff) <= threshold:
                    return base_delta + diff, active
                self._alignment_snap_state[state_key] = None

            if not guides:
                return base_delta, None

            best = None
            best_abs = threshold
            for idx, pos in enumerate(current):
                insert_at = bisect_left(guides, pos)
                for guide_index in (insert_at - 1, insert_at):
                    if 0 <= guide_index < len(guides):
                        guide = guides[guide_index]
                        diff = guide - pos
                        ad = abs(diff)
                        if ad <= best_abs:
                            best_abs = ad
                            best = (guide, idx, diff)
            if best is None:
                return base_delta, None

            active = (best[0], best[1])
            self._alignment_snap_state[state_key] = active
            return base_delta + best[2], active

        def _update_alignment_guides(self, x_guide, y_guide):
            """Update guide lines only when the snapped axes change."""
            desired = (x_guide, y_guide)
            if desired == getattr(self, "_alignment_rendered_guides", (None, None)):
                return
            self._clear_alignment_guides(reset_snap=False)
            self._alignment_rendered_guides = desired
            z = self._zoom or 1.0
            if x_guide is not None:
                x = x_guide[0] * z
                self._alignment_guide_ids.append(
                    self.canvas.create_line(
                        x, 0, x, self.CANVAS_H * z,
                        fill="#607D8B", dash=(4, 4), width=1,
                        tags=("alignment_guide",)
                    )
                )
            if y_guide is not None:
                y = y_guide[0] * z
                self._alignment_guide_ids.append(
                    self.canvas.create_line(
                        0, y, self.CANVAS_W * z, y,
                        fill="#607D8B", dash=(4, 4), width=1,
                        tags=("alignment_guide",)
                    )
                )
            # Keep guides above the canvas surface/background but below widgets.
            try:
                self.canvas.tag_raise("alignment_guide", "canvas_surface")
                if self.canvas.find_withtag("canvas_background"):
                    self.canvas.tag_raise("alignment_guide", "canvas_background")
            except tk.TclError:
                self.canvas.tag_lower("alignment_guide")

        def _reset_drag_state(self, keep_selection_drag=False):
            self._clear_alignment_guides()
            self.drag_mode, self.drag_elem, self.mouse_down_pos, self.elem_origs, self.active_handle = "none", None, None, {}, None
            self._last_move_delta = (0, 0)
            self._alignment_moving_bounds = None
            self.canvas.dtag("dragging", "dragging")
            if not keep_selection_drag:
                self._selection_drag_mode = "replace"
            self._draw_canvas_handles()

        def _add_element(self, elem_type: str, x: int, y: int):
            sx, sy = self.renderer.snap_to_grid(int(x), int(y))
            w, h = ELEMENT_TYPES[elem_type]["default_size"]

            if elem_type == "StatusBar":
                # A status bar is docked, not freely placed: it always
                # spans the full canvas width and hugs the bottom edge,
                # regardless of where on the canvas the user clicked to
                # place it. It also never nests inside a container -- it's
                # always a root-level, window-wide element.
                w = self.CANVAS_W
                sx = 0
                sy = max(0, self.CANVAS_H - h)
            else:
                sx = max(0, min(sx, self.CANVAS_W - w))
                sy = max(0, min(sy, self.CANVAS_H - h))

            if self.reusable_ids:
                new_id = min(self.reusable_ids)
                self.reusable_ids.remove(new_id)
            else:
                new_id = self.next_id
                self.next_id += 1

            props = copy.deepcopy(ELEMENT_TYPES[elem_type]["defaults"])
            elem = DesignElement(elem_type=elem_type, x=sx, y=sy,
                                  props=props, elem_id=new_id, canvas_w=w,
                                  canvas_h=h
                                  )
            parent = (None if elem_type == "StatusBar"
                      else self._container_at(sx + w / 2, sy + h / 2))
            if parent is not None:
                elem.parent_id = parent.elem_id
                if parent.elem_type == "Notebook":
                    elem.parent_tab = int(
                        parent.props.get("active_tab", 0) or 0
                        )

            self.elements.append(elem)
            self._rebuild_index()

            # No more "try the cheap patch, fall back to full regen"
            # dance -- regenerating the whole designer module is always
            # safe and already cheap. The handler stub (if this element
            # type has a default event) goes into main_app.py, the one
            # file that's never regenerated wholesale.
            self._regenerate_designer_code()
            self._ensure_handler_stub(elem)

            if self._is_element_visible(elem):
                self.renderer.draw_element(elem)
                self._select_element(elem, clear=True)
            else:
                self._select_element(None, clear=True)

            self._update_code()
            self._update_element_count()
            self._update_status(f"Added {ELEMENT_TYPES[elem_type]['display']}.")
            self._save_state()

        def _resnap_status_bars(self) -> bool:
            """Keep every root-level StatusBar element docked to the
            bottom edge, full canvas width, whenever the canvas itself is
            resized -- whether that's a numeric edit in Canvas Settings
            (_apply_canvas_size_from_props) or a live drag of the canvas's
            own resize handle (_canvas_resize_preview, called on every
            mouse-move during that drag). Placement at first-add time is
            handled directly in _add_element().

            Only updates the model (x/y/canvas_w) and returns whether
            anything changed -- it deliberately does NOT redraw anything
            itself, since both callers already redraw afterward (one via
            a full _redraw_all_elements() pass on every drag step, the
            other via an explicit redraw below) and redrawing here too
            would just double the work on every mouse-move.
            """
            changed = False
            for elem in self.elements:
                if elem.elem_type != "StatusBar" or elem.parent_id is not None:
                    continue
                new_x, new_w = 0, self.CANVAS_W
                new_y = max(0, self.CANVAS_H - elem.canvas_h)
                if (elem.x, elem.y, elem.canvas_w) != (new_x, new_y, new_w):
                    elem.x, elem.y, elem.canvas_w = new_x, new_y, new_w
                    changed = True
            if changed:
                self._rebuild_index()
            return changed

        def _update_position_status(self, elem=None):
            if elem is None:
                self.position_var.set("Canvas: --, --    Size: -- × --")
                return
            parent=self._by_id.get(elem.parent_id) if elem.parent_id is not None else None
            if parent is None:
                self.position_var.set(f"Canvas: X {elem.x:.2f}, Y {elem.y:.2f}    Size: {elem.canvas_w:.2f} × {elem.canvas_h:.2f}")
            else:
                rx=elem.x-parent.x; ry=elem.y-parent.y
                self.position_var.set(f"Container: X {rx:.2f}, Y {ry:.2f}    Canvas: X {elem.x:.2f}, Y {elem.y:.2f}    Size: {elem.canvas_w:.2f} × {elem.canvas_h:.2f}")

        def _select_element(
                self, elem: Optional[DesignElement], clear: bool = True
                ):
            if clear:
                for e in self.selected_elems:
                    e.selected = False
                    self.renderer.redraw_element(e)
                self.selected_elems.clear()

            if elem and elem not in self.selected_elems:
                self.selected_elems.append(elem)
                elem.selected = True
                self.renderer.redraw_element(elem)

            self._reorder_elements()

            if len(self.selected_elems) == 1:
                self._show_properties(self.selected_elems[0])
            elif len(self.selected_elems) > 1:
                self._show_properties_multi()
            else:
                self._show_properties(None)
                self._update_position_status(None)

        def _align_selected(self, mode):
            elems=[e for e in self.selected_elems if e in self.elements]
            if not elems: return
            if len(elems)==1:
                e=elems[0]
                if e.parent_id is not None and e.parent_id in self._by_id:
                    p=self._by_id[e.parent_id]; px,py,pw,ph=p.x,p.y,p.canvas_w,p.canvas_h
                else: px,py,pw,ph=0,0,self.CANVAS_W,self.CANVAS_H
                if mode=='left': e.x=px
                elif mode=='center_h': e.x=px+(pw-e.canvas_w)/2
                elif mode=='right': e.x=px+pw-e.canvas_w
                elif mode=='top': e.y=py
                elif mode=='center_v': e.y=py+(ph-e.canvas_h)/2
                elif mode=='bottom': e.y=py+ph-e.canvas_h
            else:
                l=min(e.x for e in elems); t=min(e.y for e in elems); r=max(e.x+e.canvas_w for e in elems); b=max(e.y+e.canvas_h for e in elems)
                for e in elems:
                    if mode=='left': e.x=l
                    elif mode=='center_h': e.x=(l+r-e.canvas_w)/2
                    elif mode=='right': e.x=r-e.canvas_w
                    elif mode=='top': e.y=t
                    elif mode=='center_v': e.y=(t+b-e.canvas_h)/2
                    elif mode=='bottom': e.y=b-e.canvas_h
            for e in elems: e.x=round(max(0,min(self.CANVAS_W-e.canvas_w,e.x)),2); e.y=round(max(0,min(self.CANVAS_H-e.canvas_h,e.y)),2)
            self._redraw_all_elements(); self._update_code(); self._schedule_save()

        def _show_canvas_context_menu(self, event):
            x, y = self._logical_xy(event)
            clicked = self._find_element_at(x, y)
            if clicked is not None:
                if clicked not in self.selected_elems:
                    self._select_elements(self._group_members(clicked), "Selected group" if len(self._group_members(clicked)) > 1 else "Selected")
                target = clicked
            else:
                target = None

            menu = tk.Menu(self.root, tearoff=0)
            count = len(self.selected_elems)
            elems = list(self.selected_elems)

            if target is not None:
                menu.add_command(label="Edit Code", command=lambda: self._open_code_editor(target))
                menu.add_command(label="Select Group" if str(target.props.get("group_id", "")) else "Select Element",
                                  command=lambda: self._select_elements(self._group_members(target), "Selected group") if str(target.props.get("group_id", "")) else self._select_elements([target], "Selected"))
                menu.add_separator()

                if target.elem_type in ("LEDDigit", "LEDDisplay"):
                    menu.add_command(label="Set Display Value…", command=lambda: self._context_set_display_value(target))
                elif target.elem_type == "Gauge":
                    menu.add_command(label="Set Gauge Value…", command=lambda: self._context_set_gauge_value(target))
                elif target.elem_type == "LEDIndicator":
                    menu.add_command(label="Toggle LED", command=lambda: self._context_toggle_led(target))
                elif target.elem_type == "PushButton":
                    menu.add_command(label="Toggle Button State", command=lambda: self._context_toggle_button(target))
                elif target.elem_type in ("RadioButton", "Radiobutton"):
                    menu.add_command(label="Set Selected", command=lambda: self._context_select_radio(target))
                elif target.elem_type in CONTAINER_TYPES:
                    menu.add_command(label="Select Children", command=lambda: self._select_elements(self._elements_in_container(target.elem_id), "Selected container children"))

                menu.add_separator()
                visible = str(target.props.get("visible", "yes")).strip().lower() not in ("no", "0", "false")
                menu.add_command(label="Hide" if visible else "Show", command=lambda: self._context_toggle_visible(target))

            align_menu=tk.Menu(menu,tearoff=0)
            for label,mode in (("Left","left"),("Center Horizontally","center_h"),("Right","right"),("Top","top"),("Center Vertically","center_v"),("Bottom","bottom")):
                align_menu.add_command(label=label,command=lambda m=mode:self._align_selected(m),state=(tk.NORMAL if elems else tk.DISABLED))
            menu.add_cascade(label="Align",menu=align_menu,state=(tk.NORMAL if elems else tk.DISABLED))
            menu.add_separator()
            menu.add_command(label="Copy", command=self._copy_elements, state=(tk.NORMAL if elems else tk.DISABLED))
            menu.add_command(label="Paste", command=self._paste_elements, state=(tk.NORMAL if self.clipboard else tk.DISABLED))
            menu.add_command(label="Delete", command=self._delete_selected, state=(tk.NORMAL if elems else tk.DISABLED))
            menu.add_separator()
            if count >= 2:
                menu.add_command(label="Group Selected", command=self._context_group_selected)
            else:
                menu.add_command(label="Group Selected", command=self._context_group_selected, state=tk.DISABLED)
            grouped = any(str(e.props.get("group_id", "") or "").strip() for e in elems)
            menu.add_command(label="Ungroup Selected", command=self._context_ungroup_selected, state=(tk.NORMAL if grouped else tk.DISABLED))
            menu.add_separator()
            menu.add_command(label="Bring to Front", command=self._context_bring_front, state=(tk.NORMAL if elems else tk.DISABLED))
            menu.add_command(label="Send to Back", command=self._context_send_back, state=(tk.NORMAL if elems else tk.DISABLED))
            menu.tk_popup(event.x_root, event.y_root)

        def _context_group_selected(self):
            if len(self.selected_elems) < 2:
                return
            gid = self._group_elements(self.selected_elems)
            if gid:
                self._show_properties_multi()
                self._update_status(f"Grouped {len(self.selected_elems)} elements as Group {gid}.")

        def _context_ungroup_selected(self):
            if self._ungroup_elements(self.selected_elems):
                for elem in self.selected_elems:
                    self.renderer.redraw_element(elem)
                self._show_properties_multi() if len(self.selected_elems) > 1 else self._show_properties(self.selected_elems[0])
                self._update_status("Selection ungrouped.")

        def _context_toggle_visible(self, elem):
            current = str(elem.props.get("visible", "yes")).strip().lower() not in ("no", "0", "false")
            elem.props["visible"] = "No" if current else "Yes"
            self.renderer.redraw_element(elem)
            self._update_code()
            self._show_properties(elem)
            self._schedule_save()

        def _context_set_display_value(self, elem):
            value = simpledialog.askstring("LED Display Value", "Enter display value:", initialvalue=str(elem.props.get("value", "0")), parent=self.root)
            if value is not None:
                elem.props["value"] = value
                self.renderer.redraw_element(elem)
                self._update_code()
                self._show_properties(elem)
                self._schedule_save()

        def _context_set_gauge_value(self, elem):
            value = simpledialog.askfloat("Gauge Value", "Enter gauge value:", initialvalue=float(elem.props.get("value", 50)), parent=self.root)
            if value is not None:
                elem.props["value"] = value
                self.renderer.redraw_element(elem)
                self._update_code()
                self._show_properties(elem)
                self._schedule_save()

        def _context_toggle_led(self, elem):
            on = str(elem.props.get("state", "Off")).strip().lower() in ("on", "yes", "1", "true")
            elem.props["state"] = "Off" if on else "On"
            self.renderer.redraw_element(elem)
            self._update_code()
            self._show_properties(elem)
            self._schedule_save()

        def _context_toggle_button(self, elem):
            on = str(elem.props.get("default_state", "Off")).strip().lower() in ("on", "yes", "1", "true")
            elem.props["default_state"] = "Off" if on else "On"
            self.renderer.redraw_element(elem)
            self._update_code()
            self._show_properties(elem)
            self._schedule_save()

        def _context_select_radio(self, elem):
            elem.props["selected"] = "Yes"
            self.renderer.redraw_element(elem)
            self._update_code()
            self._show_properties(elem)
            self._schedule_save()

        def _context_bring_front(self):
            for elem in self.selected_elems:
                if elem in self.elements:
                    self.elements.remove(elem)
                    self.elements.append(elem)
            self._redraw_all_elements()
            self._schedule_save()

        def _context_send_back(self):
            for elem in reversed(self.selected_elems):
                if elem in self.elements:
                    self.elements.remove(elem)
                    self.elements.insert(0, elem)
            self._redraw_all_elements()
            self._schedule_save()

        def _copy_elements(self, event=None):
            widget = getattr(event, "widget", None) if event is not None else None
            if widget is not None and self._is_text_input_widget(widget):
                return
            if not self.selected_elems:
                return "break"
            self.clipboard = [e.clone_persistent() for e in self.selected_elems]
            self._update_status(
                f"Copied {len(self.clipboard)} element(s) to clipboard."
                )
            return "break"

        def _paste_elements(self, event=None):
            widget = getattr(event, "widget", None) if event is not None else None
            if widget is not None and self._is_text_input_widget(widget):
                return
            if not self.clipboard:
                return "break"
            self._select_element(None, clear=True)

            pasted = []
            pasted_id_map = {}
            pasted_group_map = {}
            for data in self.clipboard:
                new_elem = data.clone_persistent()
                old_elem_id = new_elem.elem_id
                if self.reusable_ids:
                    new_elem.elem_id = min(self.reusable_ids)
                    self.reusable_ids.remove(new_elem.elem_id)
                else:
                    new_elem.elem_id = self.next_id
                    self.next_id += 1
                pasted_id_map[old_elem_id] = new_elem.elem_id
                old_group = str(new_elem.props.get("group_id", "") or "").strip()
                if old_group:
                    if old_group not in pasted_group_map:
                        pasted_group_map[old_group] = self._new_group_id()
                    new_elem.props["group_id"] = pasted_group_map[old_group]
                new_elem.x += 20
                new_elem.y += 20
                new_elem.rect_id = 0
                new_elem.text_id = 0
                new_elem.handle_ids = {}
                new_elem.selected = False
                new_elem.parent_id = None
                self.elements.append(new_elem)
                pasted.append(new_elem)

            # Preserve Scrollbar -> Text/Canvas relationships when the target
            # and scrollbar are copied together. Relationships to widgets that
            # were not copied remain pointed at the original widget.
            for new_elem in pasted:
                if new_elem.elem_type == "Scrollbar":
                    raw_target = new_elem.props.get("target_widget", "")
                    try:
                        old_target_id = int(raw_target)
                    except (TypeError, ValueError):
                        continue
                    if old_target_id in pasted_id_map:
                        new_elem.props["target_widget"] = str(
                            pasted_id_map[old_target_id]
                        )

            self._rebuild_index()
            for new_elem in pasted:
                if self._is_element_visible(new_elem):
                    self.renderer.draw_element(new_elem)

            self._regenerate_designer_code()
            for e in pasted:
                self._ensure_handler_stub(e)

            for e in pasted:
                if self._is_element_visible(e):
                    self._select_element(e, clear=False)

            self._update_code()
            self._update_element_count()
            self._update_status(f"Pasted {len(pasted)} element(s).")
            self._save_state()
            return "break"

        def _delete_selected(self, event=None):
            if event and hasattr(event, "widget") and event.widget.winfo_class() in ("Entry",
                                                                                     "TEntry",
                                                                                     "Text"):
                return

            if not self.selected_elems:
                return

            if not messagebox.askyesno("Confirm Deletion",
                                        "Are you sure you want to delete the selected element(s)?\nNote: Deleting a Container deletes all enclosed children elements."
                                        ):
                return

            to_delete = list(self.selected_elems)

            for elem in self.selected_elems:
                if elem.elem_type in CONTAINER_TYPES:
                    for child in self._children_by_parent.get(elem.elem_id, []):
                        if child not in to_delete:
                            to_delete.append(child)

            deleted_ids = {e.elem_id for e in to_delete}
            deleted_id_strings = {str(v) for v in deleted_ids}
            for remaining in self.elements:
                if (remaining.elem_type == "Scrollbar" and
                        str(remaining.props.get("target_widget", "")).strip()
                        in deleted_id_strings):
                    remaining.props["target_widget"] = ""
                if (remaining.elem_type == "LEDIndicator" and
                        str(remaining.props.get("source_widget", "")).strip()
                        in deleted_id_strings):
                    remaining.props["source_widget"] = ""

            for elem in to_delete:
                self.renderer.erase_element(elem)
                if elem in self.elements:
                    self.elements.remove(elem)
                    self.reusable_ids.add(elem.elem_id)
            self._rebuild_index()

            # A single unconditional regenerate replaces the old
            # special_runtime_types / removed_scroll_relation dance --
            # there's no cheaper splice path left to fall back FROM.
            # Deliberately does not touch self.user_code: any handler
            # method belonging to a deleted element is left in place,
            # orphaned, exactly as a WinForms designer leaves an unused
            # event handler in code-behind after you delete the control
            # that used to raise it, rather than risk deleting something
            # the user had since added to that method's body.
            self._regenerate_designer_code()

            self.selected_elems.clear()
            self._reset_drag_state()
            self._show_properties(None)
            self._update_code()
            self._update_element_count()
            self._update_status("Element(s) deleted.")
            self._save_state()

        def _clear_all(self):
            if not self.elements:
                return
            if not messagebox.askyesno("Confirm Clear",
                                        "Are you sure you want to clear the entire canvas? All unsaved progress will be lost."
                                        ):
                return

            for elem in self.elements:
                self.renderer.erase_element(elem)
            self.elements.clear()
            self._rebuild_index()
            self.selected_elems.clear()
            self.reusable_ids.clear()
            self.next_id = 1

            self._reset_drag_state()
            self.canvas.delete("all")
            self.renderer.draw_canvas_background(self.CANVAS_BG_IMAGE, self.CANVAS_BG_IMAGE_MODE, self.CANVAS_BG_IMAGE_ANCHOR, self.CANVAS_W, self.CANVAS_H)
            self.renderer.draw_canvas_border(self.CANVAS_W, self.CANVAS_H)
            self._show_properties(None)
            self._regenerate_designer_code()
            self._update_code()
            self._update_element_count()
            self._save_state()
