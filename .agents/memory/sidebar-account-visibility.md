---
name: Sidebar account visibility
description: User requirement for persistent account visibility during sidebar scrolling.
---

The logged-in organization/account must remain stationary at the bottom of the visible sidebar while navigation and settings scroll independently.

**Why:** The user explicitly rejected both bottom alignment in the scrolling content and a sticky footer that still moved during scrolling. “At the bottom” means persistently visible, not the end of the sidebar document.

**How to apply:** Preserve this behavior in sidebar changes. Verify by actually scrolling with settings expanded on short screens, not just taking a static screenshot.
