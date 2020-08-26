--
-- PostgreSQL database dump
--

-- Dumped from database version 11.7 (Debian 11.7-0+deb10u1)
-- Dumped by pg_dump version 11.7 (Debian 11.7-0+deb10u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO crax;

--
-- Name: customer_a; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.customer_a (
    ave_bill integer,
    id integer NOT NULL,
    bio character varying(100) NOT NULL,
    username character varying(50) NOT NULL,
    password character varying(250) NOT NULL,
    first_name character varying(50),
    middle_name character varying(50),
    last_name character varying(50),
    phone character varying(20),
    email character varying(150),
    is_active boolean,
    is_staff boolean,
    is_superuser boolean,
    date_joined timestamp without time zone,
    last_login timestamp without time zone,
    age integer
);


ALTER TABLE public.customer_a OWNER TO crax;

--
-- Name: customer_a_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.customer_a_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.customer_a_id_seq OWNER TO crax;

--
-- Name: customer_a_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.customer_a_id_seq OWNED BY public.customer_a.id;


--
-- Name: customer_b; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.customer_b (
    discount integer,
    customer_discount_id integer,
    id integer NOT NULL,
    bio character varying(100) NOT NULL,
    username character varying(50) NOT NULL,
    password character varying(250) NOT NULL,
    first_name character varying(50),
    middle_name character varying(50),
    last_name character varying(50),
    phone character varying(20),
    email character varying(150),
    is_active boolean,
    is_staff boolean,
    is_superuser boolean,
    date_joined timestamp without time zone,
    last_login timestamp without time zone,
    age integer
);


ALTER TABLE public.customer_b OWNER TO crax;

--
-- Name: customer_b_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.customer_b_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.customer_b_id_seq OWNER TO crax;

--
-- Name: customer_b_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.customer_b_id_seq OWNED BY public.customer_b.id;


--
-- Name: customer_discount; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.customer_discount (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    percent integer NOT NULL
);


ALTER TABLE public.customer_discount OWNER TO crax;

--
-- Name: customer_discount_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.customer_discount_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.customer_discount_id_seq OWNER TO crax;

--
-- Name: customer_discount_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.customer_discount_id_seq OWNED BY public.customer_discount.id;


--
-- Name: group_permissions; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.group_permissions (
    group_id integer,
    permission_id integer,
    id integer NOT NULL
);


ALTER TABLE public.group_permissions OWNER TO crax;

--
-- Name: group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.group_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.group_permissions_id_seq OWNER TO crax;

--
-- Name: group_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.group_permissions_id_seq OWNED BY public.group_permissions.id;


--
-- Name: groups; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.groups (
    name character varying(100) NOT NULL,
    id integer NOT NULL
);


ALTER TABLE public.groups OWNER TO crax;

--
-- Name: groups_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.groups_id_seq OWNER TO crax;

--
-- Name: groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.groups_id_seq OWNED BY public.groups.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.orders (
    staff character varying(100) NOT NULL,
    price integer NOT NULL,
    customer_id integer,
    vendor_id integer,
    id integer NOT NULL
);


ALTER TABLE public.orders OWNER TO crax;

--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.orders_id_seq OWNER TO crax;

--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.orders_id_seq OWNED BY public.orders.id;


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.permissions (
    name character varying(100) NOT NULL,
    model character varying(50) NOT NULL,
    can_read boolean,
    can_write boolean,
    can_create boolean,
    can_delete boolean,
    id integer NOT NULL
);


ALTER TABLE public.permissions OWNER TO crax;

--
-- Name: permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.permissions_id_seq OWNER TO crax;

--
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- Name: user_groups; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.user_groups (
    user_id integer,
    group_id integer,
    id integer NOT NULL
);


ALTER TABLE public.user_groups OWNER TO crax;

--
-- Name: user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.user_groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_groups_id_seq OWNER TO crax;

--
-- Name: user_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.user_groups_id_seq OWNED BY public.user_groups.id;


--
-- Name: user_info; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.user_info (
    age integer,
    id integer NOT NULL
);


ALTER TABLE public.user_info OWNER TO crax;

--
-- Name: user_info_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.user_info_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_info_id_seq OWNER TO crax;

--
-- Name: user_info_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.user_info_id_seq OWNED BY public.user_info.id;


--
-- Name: user_permissions; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.user_permissions (
    user_id integer,
    permission_id integer,
    id integer NOT NULL
);


ALTER TABLE public.user_permissions OWNER TO crax;

--
-- Name: user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.user_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_permissions_id_seq OWNER TO crax;

--
-- Name: user_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.user_permissions_id_seq OWNED BY public.user_permissions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.users (
    username character varying(50) NOT NULL,
    password character varying(250) NOT NULL,
    first_name character varying(50),
    middle_name character varying(50),
    last_name character varying(50),
    phone character varying(20),
    email character varying(150),
    is_active boolean,
    is_staff boolean,
    is_superuser boolean,
    date_joined timestamp without time zone,
    last_login timestamp without time zone,
    id integer NOT NULL
);


ALTER TABLE public.users OWNER TO crax;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 10
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO crax;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: vendor; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.vendor (
    vendor_discount_id integer,
    id integer NOT NULL,
    bio character varying(100) NOT NULL,
    username character varying(50) NOT NULL,
    password character varying(250) NOT NULL,
    first_name character varying(50),
    middle_name character varying(50),
    last_name character varying(50),
    phone character varying(20),
    email character varying(150),
    is_active boolean,
    is_staff boolean,
    is_superuser boolean,
    date_joined timestamp without time zone,
    last_login timestamp without time zone,
    age integer
);


ALTER TABLE public.vendor OWNER TO crax;

--
-- Name: vendor_discount; Type: TABLE; Schema: public; Owner: crax
--

CREATE TABLE public.vendor_discount (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    percent integer NOT NULL
);


ALTER TABLE public.vendor_discount OWNER TO crax;

--
-- Name: vendor_discount_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.vendor_discount_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.vendor_discount_id_seq OWNER TO crax;

--
-- Name: vendor_discount_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.vendor_discount_id_seq OWNED BY public.vendor_discount.id;


--
-- Name: vendor_id_seq; Type: SEQUENCE; Schema: public; Owner: crax
--

CREATE SEQUENCE public.vendor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.vendor_id_seq OWNER TO crax;

--
-- Name: vendor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crax
--

ALTER SEQUENCE public.vendor_id_seq OWNED BY public.vendor.id;


--
-- Name: customer_a id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.customer_a ALTER COLUMN id SET DEFAULT nextval('public.customer_a_id_seq'::regclass);


--
-- Name: customer_b id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.customer_b ALTER COLUMN id SET DEFAULT nextval('public.customer_b_id_seq'::regclass);


--
-- Name: customer_discount id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.customer_discount ALTER COLUMN id SET DEFAULT nextval('public.customer_discount_id_seq'::regclass);


--
-- Name: group_permissions id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.group_permissions ALTER COLUMN id SET DEFAULT nextval('public.group_permissions_id_seq'::regclass);


--
-- Name: groups id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.groups ALTER COLUMN id SET DEFAULT nextval('public.groups_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.orders ALTER COLUMN id SET DEFAULT nextval('public.orders_id_seq'::regclass);


--
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- Name: user_groups id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.user_groups ALTER COLUMN id SET DEFAULT nextval('public.user_groups_id_seq'::regclass);


--
-- Name: user_info id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.user_info ALTER COLUMN id SET DEFAULT nextval('public.user_info_id_seq'::regclass);


--
-- Name: user_permissions id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.user_permissions ALTER COLUMN id SET DEFAULT nextval('public.user_permissions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: vendor id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.vendor ALTER COLUMN id SET DEFAULT nextval('public.vendor_id_seq'::regclass);


--
-- Name: vendor_discount id; Type: DEFAULT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.vendor_discount ALTER COLUMN id SET DEFAULT nextval('public.vendor_discount_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.alembic_version (version_num) FROM stdin;
fafdc47fb45f
8f98b292611c
\.


--
-- Data for Name: customer_a; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.customer_a (ave_bill, id, bio, username, password, first_name, middle_name, last_name, phone, email, is_active, is_staff, is_superuser, date_joined, last_login, age) FROM stdin;
\.


--
-- Data for Name: customer_b; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.customer_b (discount, customer_discount_id, id, bio, username, password, first_name, middle_name, last_name, phone, email, is_active, is_staff, is_superuser, date_joined, last_login, age) FROM stdin;
\.


--
-- Data for Name: customer_discount; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.customer_discount (id, name, percent) FROM stdin;
\.


--
-- Data for Name: group_permissions; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.group_permissions (group_id, permission_id, id) FROM stdin;
\.


--
-- Data for Name: groups; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.groups (name, id) FROM stdin;
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.orders (staff, price, customer_id, vendor_id, id) FROM stdin;
\.


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.permissions (name, model, can_read, can_write, can_create, can_delete, id) FROM stdin;
\.


--
-- Data for Name: user_groups; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.user_groups (user_id, group_id, id) FROM stdin;
\.


--
-- Data for Name: user_info; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.user_info (age, id) FROM stdin;
\.


--
-- Data for Name: user_permissions; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.user_permissions (user_id, permission_id, id) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.users (username, password, first_name, middle_name, last_name, phone, email, is_active, is_staff, is_superuser, date_joined, last_login, id) FROM stdin;
mark	76b5dc3a1e1b8eb7c5533c7dab83ec614b587f4701b041f282d944c7b483f895	Mark	\N	\N	\N	\N	t	t	t	\N	\N	1
joe	76b5dc3a1e1b8eb7c5533c7dab83ec614b587f4701b041f282d944c7b483f895	Joe	\N	\N	\N	\N	t	f	f	\N	\N	2
\.


--
-- Data for Name: vendor; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.vendor (vendor_discount_id, id, bio, username, password, first_name, middle_name, last_name, phone, email, is_active, is_staff, is_superuser, date_joined, last_login, age) FROM stdin;
\.


--
-- Data for Name: vendor_discount; Type: TABLE DATA; Schema: public; Owner: crax
--

COPY public.vendor_discount (id, name, percent) FROM stdin;
\.


--
-- Name: customer_a_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.customer_a_id_seq', (SELECT MAX(id) FROM customer_a)+1, false);


--
-- Name: customer_b_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.customer_b_id_seq', (SELECT MAX(id) FROM customer_b)+1, false);


--
-- Name: customer_discount_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.customer_discount_id_seq', (SELECT MAX(id) FROM customer_discount)+1, false);


--
-- Name: group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.group_permissions_id_seq',  (SELECT MAX(id) FROM group_permissions)+1, false);


--
-- Name: groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.groups_id_seq',  (SELECT MAX(id) FROM groups)+1, false);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.orders_id_seq',  (SELECT MAX(id) FROM orders)+1, false);


--
-- Name: permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.permissions_id_seq',  (SELECT MAX(id) FROM permissions)+1, false);


--
-- Name: user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.user_groups_id_seq',  (SELECT MAX(id) FROM user_groups)+1, false);


--
-- Name: user_info_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.user_info_id_seq',  (SELECT MAX(id) FROM user_info)+1, false);


--
-- Name: user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.user_permissions_id_seq',  (SELECT MAX(id) FROM user_permissions)+1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.users_id_seq', (SELECT MAX(id) FROM users)+1, false);


--
-- Name: vendor_discount_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.vendor_discount_id_seq', (SELECT MAX(id) FROM vendor_discount)+1, false);


--
-- Name: vendor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: crax
--

SELECT pg_catalog.setval('public.vendor_id_seq', (SELECT MAX(id) FROM vendor)+1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: customer_a customer_a_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.customer_a
    ADD CONSTRAINT customer_a_pkey PRIMARY KEY (id);


--
-- Name: customer_b customer_b_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.customer_b
    ADD CONSTRAINT customer_b_pkey PRIMARY KEY (id);


--
-- Name: customer_discount customer_discount_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.customer_discount
    ADD CONSTRAINT customer_discount_pkey PRIMARY KEY (id);


--
-- Name: group_permissions group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.group_permissions
    ADD CONSTRAINT group_permissions_pkey PRIMARY KEY (id);


--
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: user_groups user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.user_groups
    ADD CONSTRAINT user_groups_pkey PRIMARY KEY (id);


--
-- Name: user_info user_info_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.user_info
    ADD CONSTRAINT user_info_pkey PRIMARY KEY (id);


--
-- Name: user_permissions user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.user_permissions
    ADD CONSTRAINT user_permissions_pkey PRIMARY KEY (id);


--
-- Name: users username; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT username UNIQUE (username);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: vendor_discount vendor_discount_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.vendor_discount
    ADD CONSTRAINT vendor_discount_pkey PRIMARY KEY (id);


--
-- Name: vendor vendor_pkey; Type: CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.vendor
    ADD CONSTRAINT vendor_pkey PRIMARY KEY (id);


--
-- Name: customer_b customer_b_customer_discount_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.customer_b
    ADD CONSTRAINT customer_b_customer_discount_id_fkey FOREIGN KEY (customer_discount_id) REFERENCES public.customer_discount(id);


--
-- Name: group_permissions group_permissions_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.group_permissions
    ADD CONSTRAINT group_permissions_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id);


--
-- Name: group_permissions group_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.group_permissions
    ADD CONSTRAINT group_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id);


--
-- Name: orders orders_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customer_b(id);


--
-- Name: orders orders_vendor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendor(id);


--
-- Name: user_groups user_groups_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.user_groups
    ADD CONSTRAINT user_groups_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id);


--
-- Name: user_groups user_groups_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.user_groups
    ADD CONSTRAINT user_groups_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_permissions user_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.user_permissions
    ADD CONSTRAINT user_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id);


--
-- Name: user_permissions user_permissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.user_permissions
    ADD CONSTRAINT user_permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: vendor vendor_vendor_discount_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: crax
--

ALTER TABLE ONLY public.vendor
    ADD CONSTRAINT vendor_vendor_discount_id_fkey FOREIGN KEY (vendor_discount_id) REFERENCES public.vendor_discount(id);


--
-- PostgreSQL database dump complete
--

