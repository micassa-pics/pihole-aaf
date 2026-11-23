# Build with the Git repository as context. Supply the installed Pi-hole image tag or digest.
ARG PIHOLE_IMAGE
FROM ${PIHOLE_IMAGE} AS web
RUN apk add --no-cache git
COPY patches/pihole-dhcp-table.patch patches/pihole-query-log-grouping.patch lease-handoffs/web.patch lease-handoffs/guard-web.patch /tmp/patches/
WORKDIR /var/www/html/admin
RUN git apply /tmp/patches/pihole-dhcp-table.patch && git apply /tmp/patches/pihole-query-log-grouping.patch

FROM web AS handoff-web
RUN git apply /tmp/patches/web.patch

FROM handoff-web AS guard-web
RUN git apply /tmp/patches/guard-web.patch
COPY lease-handoffs/reservation-ui.js scripts/js/reservation-ui.js

FROM ${PIHOLE_IMAGE} AS runtime
RUN mkdir -p /jail/etc/apk /jail/app /jail/config /jail/state && cp -R /etc/apk/keys /etc/apk/repositories /jail/etc/apk/ && apk --root /jail --initdb --no-cache --no-scripts add python3
COPY lease-handoffs/docker/drop.py lease-handoffs/checkpoint.py /jail/app/

FROM ${PIHOLE_IMAGE} AS pages
COPY --from=web /var/www/html/admin/ /var/www/html/admin/

FROM pages AS handoffs
COPY --from=handoff-web /var/www/html/admin/ /var/www/html/admin/
# Match the monitor's read-only Docker publication mount. Native installs can
# continue using the path in web.patch.
RUN sed -i 's|/etc/pihole/lease-handoffs/view.txt|/run/pihole-lease-handoffs/view.txt|' /var/www/html/admin/lease-handoffs.lp
COPY --from=runtime /jail /opt/monitor
COPY lease-handoffs/worker.py /opt/monitor/app/
COPY lease-handoffs/docker/readiness.py /opt/monitor/app/
COPY lease-handoffs/docker/start /usr/local/bin/start-handoffs
COPY lease-handoffs/docker/health /usr/local/bin/health-handoffs
RUN chmod 0755 /usr/local/bin/start-handoffs /usr/local/bin/health-handoffs && chmod 0644 /opt/monitor/app/*.py
HEALTHCHECK --interval=20s --timeout=10s --start-period=45s CMD ["/usr/local/bin/health-handoffs"]
ENTRYPOINT ["/usr/local/bin/start-handoffs"]

FROM handoffs AS guarded
RUN apk add --no-cache nginx
COPY --from=guard-web /var/www/html/admin/ /var/www/html/admin/
COPY --from=runtime /jail /opt/guard
COPY lease-handoffs/guard.py /opt/guard/app/
COPY lease-handoffs/guard-nginx.location /etc/nginx/guard.location
COPY lease-handoffs/docker/nginx.conf /etc/nginx/nginx.conf
RUN chmod 0644 /opt/guard/app/*.py /etc/nginx/nginx.conf /etc/nginx/guard.location /var/www/html/admin/scripts/js/reservation-ui.js

FROM pages AS default
