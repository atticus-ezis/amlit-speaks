# Optimize streaming

I'm hard-capped at 6 concurrent streams through elevenlabs turbo_flash_v2.
I want to get that to ~10

# problem

- Each labs-connection needs to terminate before handling next request. That means that a user has to wait for the entirety of the previous user's text to finish generating before they can be served.
- At this stage fastapi's event loop only helps serve those 6 labs-connections concurrently. If 7+ users wait for too long they risk being dropped or timed out.

# strategy

- Split text into smaller fragments which terminate independenlty and frees the labs-connection faster.
- In order to track these text-fragments and make sure they're returned to the right user in the right order - I will use a message-broker queue like redis to track the stream_id across each text-fragment.
- Switch to web-socket instead of http chunked streaming. Lowers latency from http requests, now redis can push instantly. Better control, user's can be paused, canacled and re-prioritized later.

# useful stats:

1 min == 1,000 characters (generation time)
200 words == 1,000 characters

50 words == ~ 26 seconds (speaking time)
50 words == ~ 15 seconds (generation time)
