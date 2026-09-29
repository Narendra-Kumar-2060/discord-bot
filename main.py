import os
import staypresent

# Create a simple web endpoint so Render is happy
staypresent.web.json({"status": "running"})

# Run your actual bot code from bot.py
staypresent.run("bot.py", port=int(os.getenv("PORT", 8080)))
