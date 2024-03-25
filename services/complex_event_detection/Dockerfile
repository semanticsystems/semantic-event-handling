#
# Build stage
#
FROM eclipse-temurin:17-jdk-jammy AS build
ENV HOME=/usr/app
RUN mkdir -p $HOME
WORKDIR $HOME
COPY . $HOME
RUN --mount=type=cache,target=/root/.m2 ./mvnw -f $HOME/pom.xml clean package

#
# Package stage
#
FROM eclipse-temurin:17-jre-jammy 
ARG JAR_FILE=/usr/app/target/*-jar-with-dependencies.jar
COPY --from=build $JAR_FILE /app/runner.jar
COPY config /app/config
COPY data /app/data
EXPOSE 8080
WORKDIR /app
ENTRYPOINT java -jar /app/runner.jar -c /app/config/config.docker.json