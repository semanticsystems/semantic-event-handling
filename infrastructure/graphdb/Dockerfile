FROM ontotext/graphdb:10.4.0

ENV GDB_JAVA_OPTS "-Xmx3g -Xms3g \
        -Dgraphdb.home=/opt/graphdb/home \
        -Dgraphdb.workbench.importDirectory=/opt/graphdb/import \
        -Dgraphdb.workbench.cors.enable=true \
        -Denable-context-index=true \
        -Dentity-pool-implementation=transactional \
        -Dhealth.max.query.time.seconds=60 \
        -Dgraphdb.append.request.id.headers=true \
        -Dreuse.vars.in.subselects=true"

# Repository Configuration
COPY graphdb_repo_config.ttl /opt/graphdb/graphdb_repo_config.ttl

# Copy triples to container
COPY sense.ttl /opt/graphdb/import/
COPY semanticmodel.ttl /opt/graphdb/import/

# Import triples
RUN /opt/graphdb/dist/bin/importrdf preload --force --recursive -q /tmp -c /opt/graphdb/graphdb_repo_config.ttl /opt/graphdb/import

ENTRYPOINT ["/opt/graphdb/dist/bin/graphdb"]