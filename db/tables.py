"""

create table settings(
    id serial primary key,
    uname varchar(255),
    passwd varchar(255),
    post_count int default 10
);


create table process(
    id serial primary key,
    name varchar(255),
    status int default 1,
    start_time timestamp,
    end_time timestamp,
    items varchar[]
);


create table results(
    id serial primary key,
    process_id int,
    result jsonb
);


"""