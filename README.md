# Building UC Data

TODO

## Running the System

This project leverages docker-compose to orchestrate its services. The services are organized into three distinct categories: infrastructure, project, and scenario.

In the infrastructure category, you'll find third-party applications essential for our system's seamless operation. Take, for example, the GraphDb instance responsible for hosting the knowledge base.

Moving up the stack, the project layer encompasses applications developed within the project. These applications build upon the foundation laid by the infrastructure layer, delivering the full functionality of this project.

Finally, the scenario layer executes specific scenario by emitting sensor values. This feature allows you to effortlessly simulate the entire setup with real sensor data using a single command. In a real-world deployment this category will **not** be included.

To simplify the process, each layer corresponds to a docker-compose profile. For instance, to initiate the infrastructure layer, execute `COMPOSE_PROFILES=infrastructure docker-compose up`. Alternatively, you can employ the convenient scripts located in the project's root folder to execute these commands.

## Running Services on the Host

Most things work fine as there are two configuration files - one for running it within a container and one for running it on the host. We do not have such a thing for the information stored in the knowledge base. Here we must update the address of the InluxDB manually to use the "localhost". Use the following SPARQL Statements:

```
PREFIX ref: <https://brickschema.org/schema/Brick/ref#>
PREFIX : <http://auto.tuwien.ac.at/example#>
DELETE WHERE {
    :db ref:address ?oldAddress .
}
```

```
PREFIX ref: <https://brickschema.org/schema/Brick/ref#>
PREFIX : <http://auto.tuwien.ac.at/example#>
INSERT DATA {
    :db ref:address "localhost" .
}
```