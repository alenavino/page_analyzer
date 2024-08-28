DROP TABLE IF EXISTS urls;

DROP TABLE IF EXISTS url_checks;

DROP TABLE IF EXISTS last_url_checks;

CREATE TABLE urls (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at DATE NOT NULL
);

CREATE TABLE url_checks (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id BIGINT,
    status_code INT,
    h1 VARCHAR(512),
    title VARCHAR(512),
    description VARCHAR(512),
    created_at DATE NOT NULL
);

CREATE TABLE last_url_checks (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id BIGINT,
    status_code INT,
    h1 VARCHAR(512),
    title VARCHAR(512),
    description VARCHAR(512),
    created_at DATE NOT NULL
);