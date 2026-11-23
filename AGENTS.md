# Docker deployment

Keep each patch and its runtime processes inside the Pi-hole image and container. Use a derived image for extra dependencies. Keep configuration, checkpoints and journals on persistent volumes. Use a second helper container only when a verified technical constraint makes the same-container design impossible. Record the constraint before changing the deployment.
