# External Co-review Protocol

The authorization and reviewer selection are defined by `review-code`. This
protocol owns one bounded invocation of the configured reviewer.

1. Finish the independent primary review before constructing the packet. Do not
   put primary-review findings in the packet.
2. Decide the requested scope yourself by inspecting Git state, diffs, relevant
   files, call sites, tests, and applicable repository instructions.
3. Construct one self-contained Markdown packet with only the evidence the
   reviewer needs. Include the selected change, enough current source and
   context to verify it, applicable instructions, and path/line anchors. Exclude
   credentials, unrelated files, generated output, and binary data. Keep the
   packet below 1,500,000 bytes.
4. Freeze those exact bytes in a new regular temporary file outside the
   repository. Tell the user that this packet will be sent to the configured
   reviewer. If the execution environment blocks outbound network access,
   request the minimum permission needed before invoking; do not spend the
   single invocation on a known network-blocked attempt. Then invoke exactly
   once:

   ```sh
   worklore _co-review --packet ABSOLUTE_PACKET_PATH
   ```

   If the permission gate requires explicit user approval before starting the
   command, delete the temporary packet and report a paused co-review. After the
   user approves, verify that the reviewed snapshot is unchanged, reconstruct
   and freeze the packet, then continue at the invocation above. Do not repeat
   the primary review or count the blocked preflight as the one provider
   invocation. If the user declines, report an incomplete audit.
5. The helper reads the configured reviewer from settings. If it is missing,
   unavailable, unauthenticated, times out, exits nonzero, or returns no output,
   report an incomplete audit. Do not install, authenticate, retry, or fall back.
6. Delete the temporary packet. Reproduce each candidate against the repository,
   deduplicate it against the primary review, and report the returned packet
   hash with verified and rejected candidates and remaining audit gaps.

The helper only bounds, scans, hashes, and transports the frozen packet. It
runs the reviewer in an isolated temporary directory containing only those
bytes. It does not choose scope, inspect the repository, render Markdown, probe
provider identity, or grant the reviewer authority over the final report. It
supplies [co-review-prompt.md](co-review-prompt.md) as the review policy; do not
duplicate that policy inside the packet.
