# Simple Dockerfile for testing FixShell build mode
FROM alpine:latest
RUN echo "FixShell Build Test Successful"
CMD ["echo", "Hello from FixShell"]
