# Archive of community.oshwa.org

This is a read-only archive of the Discourse forum that lived at community.oshwa.org. It is viewable at https://community-archive.oshwa.org.

## Notes

- The archived data lives in `.json` format under `data/`.
- The archive website is generated from the data using `uv run -- python3 scripts/build.py`. If you need to modify the archive output, the page templates are in `scripts/templates`.
- The archive website is deployed to GitHub pages, though our deployment action does not automatically rebuild the site from the data and templates, so commit your changes to `www` to see them deployed.
- The archived data was created using `uv run -- python3 scripts/export.py` and by manually grabbing all of the uploads from the Discourse server. Since the server is no longer running, it's no longer possible to run this script. There is a full backup of the database in the OSHWA drive if needed.
