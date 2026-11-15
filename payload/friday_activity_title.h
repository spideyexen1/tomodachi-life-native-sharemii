/* SPDX-License-Identifier: GPL-3.0-only */
#ifndef FRIDAY_ACTIVITY_TITLE_H
#define FRIDAY_ACTIVITY_TITLE_H
#include <stdlib.h>

/* Discord's normal game detection can mistake the FPS suffix for a name.
 * The integration launcher supplies a stable title; direct diagnostic runs
 * keep the upstream frame/loading title when this variable is absent/empty.
 * This neither connects to Discord nor changes its sharing preferences. */
static const char *friday_activity_title(const char *diagnostic_title) {
    const char *title = getenv("TOMO_DISCORD_TITLE");
    return title && title[0] ? title : diagnostic_title;
}
#endif
