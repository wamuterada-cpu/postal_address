select * from prod.population_data;

truncate prod.population_data;

insert into prod.population_data select * from dev.population_data;

create or replace procedure dev.sp_delete_target_data("都道府県コード"text)
language plpgsql
as $$
#variable_conflict use_variable
begin
delete from dev.population_data
where "都道府県コード"="都道府県コード"
and "人口区分"='日本人人口'
and "性別"='男女計';
commit;
end;
$$;

CALL dev.sp_delete_target_data('36000');

select * from dev.population_data
where "都道府県コード"='36000'
and "人口区分"='日本人人口'
and "性別"='男女計';
