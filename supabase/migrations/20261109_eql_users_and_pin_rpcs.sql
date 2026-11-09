-- Exam trainer storage: one closed table + PIN-checked functions.
-- Applied to Supabase project "eql-exam-trainer" (xvqakxisxwhyewmhgcjt).
create extension if not exists pgcrypto with schema extensions;

create table public.eql_users (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(btrim(name)) between 1 and 40),
  pin_hash text not null,
  progress jsonb not null default '{}'::jsonb,
  failed_attempts int not null default 0,
  locked_until timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index eql_users_name_lower on public.eql_users (lower(btrim(name)));
alter table public.eql_users enable row level security;   -- no policies: no direct access
revoke all on public.eql_users from anon, authenticated;

create or replace function public._eql_check(p_name text, p_pin text, out uid uuid, out reason text)
language plpgsql security definer set search_path = '' as $$
declare u public.eql_users%rowtype;
begin
  select * into u from public.eql_users where lower(btrim(name)) = lower(btrim(p_name)) for update;
  if not found then reason := 'unknown_name'; return; end if;
  if u.locked_until is not null and u.locked_until > now() then reason := 'locked'; return; end if;
  if u.pin_hash = extensions.crypt(coalesce(p_pin,''), u.pin_hash) then
    if u.failed_attempts > 0 then update public.eql_users set failed_attempts = 0, locked_until = null where id = u.id; end if;
    uid := u.id; return;
  end if;
  if u.failed_attempts + 1 >= 5 then
    update public.eql_users set failed_attempts = 0, locked_until = now() + interval '15 minutes' where id = u.id;
    reason := 'locked';
  else
    update public.eql_users set failed_attempts = u.failed_attempts + 1 where id = u.id;
    reason := 'wrong_pin';
  end if;
end $$;
revoke all on function public._eql_check(text,text) from public, anon, authenticated;

create or replace function public.eql_list_names()
returns setof text language sql security definer set search_path = '' stable as $$
  select name from public.eql_users order by lower(name);
$$;

create or replace function public.eql_register(p_name text, p_pin text)
returns jsonb language plpgsql security definer set search_path = '' as $$
begin
  if p_pin is null or p_pin !~ '^[0-9]{4,6}$' then return jsonb_build_object('ok',false,'error','bad_pin'); end if;
  if p_name is null or char_length(btrim(p_name)) not between 1 and 40 then return jsonb_build_object('ok',false,'error','bad_name'); end if;
  if exists (select 1 from public.eql_users where lower(btrim(name)) = lower(btrim(p_name))) then
    return jsonb_build_object('ok',false,'error','name_taken'); end if;
  insert into public.eql_users(name, pin_hash) values (btrim(p_name), extensions.crypt(p_pin, extensions.gen_salt('bf', 8)));
  return jsonb_build_object('ok',true,'progress','{}'::jsonb);
end $$;

create or replace function public.eql_login(p_name text, p_pin text)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare c record; prog jsonb;
begin
  select * into c from public._eql_check(p_name, p_pin);
  if c.uid is null then return jsonb_build_object('ok',false,'error',c.reason); end if;
  select progress into prog from public.eql_users where id = c.uid;
  return jsonb_build_object('ok',true,'progress',prog);
end $$;

create or replace function public.eql_save(p_name text, p_pin text, p_progress jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare c record;
begin
  if p_progress is null or jsonb_typeof(p_progress) <> 'object' or pg_column_size(p_progress) > 300000 then
    return jsonb_build_object('ok',false,'error','bad_data'); end if;
  select * into c from public._eql_check(p_name, p_pin);
  if c.uid is null then return jsonb_build_object('ok',false,'error',c.reason); end if;
  update public.eql_users set progress = p_progress, updated_at = now() where id = c.uid;
  return jsonb_build_object('ok',true);
end $$;

revoke all on function public.eql_list_names(), public.eql_register(text,text), public.eql_login(text,text), public.eql_save(text,text,jsonb) from public;
grant execute on function public.eql_list_names(), public.eql_register(text,text), public.eql_login(text,text), public.eql_save(text,text,jsonb) to anon, authenticated;
