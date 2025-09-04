#!/bin/bash

# === CONFIG ===
SRC=~/dev/infra-home/
DEST=pi:/home/pi/infra-home/
EXCLUDES=(".git/" "__pycache__/" "node_modules/")
RSYNC_OPTIONS="-az --delete -v"

# Join excludes into rsync format
RSYNC_EXCLUDES=""
for e in "${EXCLUDES[@]}"; do
	RSYNC_EXCLUDES+=" --exclude=$e"
done

# === FUNCTION TO SYNC ===
sync_code() {
	echo "[$(date +'%H:%M:%S')] Syncing changes..."
	rsync $RSYNC_OPTIONS $RSYNC_EXCLUDES "$SRC" "$DEST"
	echo "[$(date +'%H:%M:%S')] Sync done."
}

# === WATCHER ===
# Using a small debounce delay (1 second) to avoid spamming rsync
DEBOUNCE_DELAY=1
LAST_RUN=0

echo "Watching $SRC for changes..."
fswatch -0 "$SRC" | while read -d "" event; do
	NOW=$(date +%s)
	# Run sync if enough time passed since last run
	if ((NOW - LAST_RUN >= DEBOUNCE_DELAY)); then
		echo "Changed: $event"
		sync_code
		LAST_RUN=$NOW
	fi
done
