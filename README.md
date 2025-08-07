# Disclaimer
This is an personal attempt at integrating Cellar Tracker to Home Assistant, I am in no way affiliated or connected to CellarTracker! LLC.

"CellarTracker!" is a trademark of CellarTracker! LLC

# Requirements
- Having an account at Cellar Tracker - https://cellartracker.com
- HACS: Home Assistant Community Store - https://hacs.xyz/
- 
- **(Optional)** secrets.yaml - https://www.home-assistant.io/docs/configuration/secrets/

# Installation
Manually add the repository to HACS 

- **Repository:** https://github.com/GuvHas/cellar_tracker
- **Category:** Integration

# Configuration:

Add your CellarTracker! username and password in `secrets.yaml`:

cellar_tracker_username: YOUR_USERNAME
cellar_tracker_password: YOUR_PASSWORD


Add the below to `configuration.yaml`

cellar_tracker:
  username:  !secret cellar_tracker_username
  password:  !secret cellar_tracker_password  
