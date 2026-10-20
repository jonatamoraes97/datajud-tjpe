begin;

alter table assunto
    alter column nome drop not null;

alter table movimento
    alter column nome drop not null;

commit;
