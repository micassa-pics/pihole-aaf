# Build with the Git repository as context. Supply the installed Pi-hole image tag or digest.
ARG PIHOLE_IMAGE
FROM ${PIHOLE_IMAGE} AS web
RUN apk add --no-cache git
COPY patches/pihole-dhcp-table.patch patches/pihole-query-log-grouping.patch lease-handoffs/web.patch lease-handoffs/guard-web.patch /tmp/patches/
WORKDIR /var/www/html/admin
RUN for patch in pihole-dhcp-table pihole-query-log-grouping web guard-web; do git apply "/tmp/patches/$patch.patch" || exit 1; done
COPY lease-handoffs/reservation-ui.js scripts/js/reservation-ui.js

FROM ${PIHOLE_IMAGE} AS runtime
RUN mkdir -p /jail/etc/apk /jail/app /jail/config /jail/state && cp -R /etc/apk/keys /etc/apk/repositories /jail/etc/apk/ && apk --root /jail --initdb --no-cache --no-scripts add python3
COPY lease-handoffs/docker/drop.py /jail/app/

FROM ${PIHOLE_IMAGE}
RUN apk add --no-cache nginx
COPY --from=web /var/www/html/admin/ /var/www/html/admin/
COPY --from=runtime /jail /opt/guard
COPY --from=runtime /jail /opt/monitor
COPY lease-handoffs/guard.py /opt/guard/app/
COPY lease-handoffs/worker.py /opt/monitor/app/
COPY lease-handoffs/guard-nginx.location /etc/nginx/guard.location
COPY lease-handoffs/docker/start /usr/local/bin/start-handoffs
RUN chmod 0755 /usr/local/bin/start-handoffs && chmod 0644 /opt/guard/app/*.py /opt/monitor/app/*.py /etc/nginx/guard.location /var/www/html/admin/scripts/js/reservation-ui.js
ENTRYPOINT ["/usr/local/bin/start-handoffs"]
