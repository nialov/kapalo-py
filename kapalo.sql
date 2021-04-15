CREATE TABLE OFFLINELAYERS (   OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   FILENAME TEXT,   VISIBLE TEXT,   OPACITY INTEGER);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE DB_VERSION (   OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   VERSION INTEGER,   UPDATED TEXT,   COMMENT TEXT);
CREATE TABLE spatial_ref_sys (
srid INTEGER NOT NULL PRIMARY KEY,
auth_name TEXT NOT NULL,
auth_srid INTEGER NOT NULL,
ref_sys_name TEXT NOT NULL DEFAULT 'Unknown',
proj4text TEXT NOT NULL,
srtext TEXT NOT NULL DEFAULT 'Undefined');
CREATE UNIQUE INDEX idx_spatial_ref_sys 
ON spatial_ref_sys (auth_srid, auth_name);
CREATE TABLE spatialite_history (
event_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
table_name TEXT NOT NULL,
geometry_column TEXT,
event TEXT NOT NULL,
timestamp TEXT NOT NULL,
ver_sqlite TEXT NOT NULL,
ver_splite TEXT NOT NULL);
CREATE TABLE geometry_columns (
f_table_name TEXT NOT NULL,
f_geometry_column TEXT NOT NULL,
geometry_type INTEGER NOT NULL,
coord_dimension INTEGER NOT NULL,
srid INTEGER NOT NULL,
spatial_index_enabled INTEGER NOT NULL,
CONSTRAINT pk_geom_cols PRIMARY KEY (f_table_name, f_geometry_column),
CONSTRAINT fk_gc_srs FOREIGN KEY (srid) REFERENCES spatial_ref_sys (srid),
CONSTRAINT ck_gc_rtree CHECK (spatial_index_enabled IN (0,1,2)));
CREATE INDEX idx_srid_geocols ON geometry_columns
(srid) ;
CREATE TRIGGER geometry_columns_f_table_name_insert
BEFORE INSERT ON 'geometry_columns'
FOR EACH ROW BEGIN
SELECT RAISE(ABORT,'insert on geometry_columns violates constraint: f_table_name value must not contain a single quote')
WHERE NEW.f_table_name LIKE ('%''%');
SELECT RAISE(ABORT,'insert on geometry_columns violates constraint: f_table_name value must not contain a double quote')
WHERE NEW.f_table_name LIKE ('%"%');
SELECT RAISE(ABORT,'insert on geometry_columns violates constraint: 
f_table_name value must be lower case')
WHERE NEW.f_table_name <> lower(NEW.f_table_name);
END;
CREATE TRIGGER geometry_columns_f_table_name_update
BEFORE UPDATE OF 'f_table_name' ON 'geometry_columns'
FOR EACH ROW BEGIN
SELECT RAISE(ABORT,'update on geometry_columns violates constraint: f_table_name value must not contain a single quote')
WHERE NEW.f_table_name LIKE ('%''%');
SELECT RAISE(ABORT,'update on geometry_columns violates constraint: f_table_name value must not contain a double quote')
WHERE NEW.f_table_name LIKE ('%"%');
SELECT RAISE(ABORT,'update on geometry_columns violates constraint: f_table_name value must be lower case')
WHERE NEW.f_table_name <> lower(NEW.f_table_name);
END;
CREATE TRIGGER geometry_columns_f_geometry_column_insert
BEFORE INSERT ON 'geometry_columns'
FOR EACH ROW BEGIN
SELECT RAISE(ABORT,'insert on geometry_columns violates constraint: f_geometry_column value must not contain a single quote')
WHERE NEW.f_geometry_column LIKE ('%''%');
SELECT RAISE(ABORT,'insert on geometry_columns violates constraint: 
f_geometry_column value must not contain a double quote')
WHERE NEW.f_geometry_column LIKE ('%"%');
SELECT RAISE(ABORT,'insert on geometry_columns violates constraint: f_geometry_column value must be lower case')
WHERE NEW.f_geometry_column <> lower(NEW.f_geometry_column);
END;
CREATE TRIGGER geometry_columns_f_geometry_column_update
BEFORE UPDATE OF 'f_geometry_column' ON 'geometry_columns'
FOR EACH ROW BEGIN
SELECT RAISE(ABORT,'update on geometry_columns violates constraint: f_geometry_column value must not contain a single quote')
WHERE NEW.f_geometry_column LIKE ('%''%');
SELECT RAISE(ABORT,'update on geometry_columns violates constraint: f_geometry_column value must not contain a double quote')
WHERE NEW.f_geometry_column LIKE ('%"%');
SELECT RAISE(ABORT,'update on geometry_columns violates constraint: f_geometry_column value must be lower case')
WHERE NEW.f_geometry_column <> lower(NEW.f_geometry_column);
END;
CREATE TRIGGER geometry_columns_geometry_type_insert
BEFORE INSERT ON 'geometry_columns'
FOR EACH ROW BEGIN
SELECT RAISE(ABORT,'geometry_type must be one of 0,1,2,3,4,5,6,7,1000,1001,1002,1003,1004,1005,1006,1007,2000,2001,2002,2003,2004,2005,2006,2007,3000,3001,3002,3003,3004,3005,3006,3007')
WHERE NOT(NEW.geometry_type IN (0,1,2,3,4,5,6,7,1000,1001,1002,1003,1004,1005,1006,1007,2000,2001,2002,2003,2004,2005,2006,2007,3000,3001,3002,3003,3004,3005,3006,3007));
END;
CREATE TRIGGER geometry_columns_geometry_type_update
BEFORE UPDATE OF 'geometry_type' ON 'geometry_columns'
FOR EACH ROW BEGIN
SELECT RAISE(ABORT,'geometry_type must be one of 0,1,2,3,4,5,6,7,1000,1001,1002,1003,1004,1005,1006,1007,2000,2001,2002,2003,2004,2005,2006,2007,3000,3001,3002,3003,3004,3005,3006,3007')
WHERE NOT(NEW.geometry_type IN (0,1,2,3,4,5,6,7,1000,1001,1002,1003,1004,1005,1006,1007,2000,2001,2002,2003,2004,2005,2006,2007,3000,3001,3002,3003,3004,3005,3006,3007));
END;
CREATE TRIGGER geometry_columns_coord_dimension_insert
BEFORE INSERT ON 'geometry_columns'
FOR EACH ROW BEGIN
SELECT RAISE(ABORT,'coord_dimension must be one of 2,3,4')
WHERE NOT(NEW.coord_dimension IN (2,3,4));
END;
CREATE TRIGGER geometry_columns_coord_dimension_update
BEFORE UPDATE OF 'coord_dimension' ON 'geometry_columns'
FOR EACH ROW BEGIN
SELECT RAISE(ABORT,'coord_dimension must be one of 2,3,4')
WHERE NOT(NEW.coord_dimension IN (2,3,4));
END;
CREATE VIEW geom_cols_ref_sys AS
SELECT f_table_name, f_geometry_column, geometry_type,
coord_dimension, spatial_ref_sys.srid AS srid,
auth_name, auth_srid, ref_sys_name, proj4text, srtext
FROM geometry_columns, spatial_ref_sys
WHERE geometry_columns.srid = spatial_ref_sys.srid
/* geom_cols_ref_sys(f_table_name,f_geometry_column,geometry_type,coord_dimension,srid,auth_name,auth_srid,ref_sys_name,proj4text,srtext) */;
CREATE TABLE spatial_ref_sys_aux (
	srid INTEGER NOT NULL PRIMARY KEY,
	is_geographic INTEGER,
	has_flipped_axes INTEGER,
	spheroid TEXT,
	prime_meridian TEXT,
	datum TEXT,
	projection TEXT,
	unit TEXT,
	axis_1_name TEXT,
	axis_1_orientation TEXT,
	axis_2_name TEXT,
	axis_2_orientation TEXT,
	CONSTRAINT fk_sprefsys FOREIGN KEY (srid) 	REFERENCES spatial_ref_sys (srid));
CREATE VIEW spatial_ref_sys_all AS
SELECT a.srid AS srid, a.auth_name AS auth_name, a.auth_srid AS auth_srid, a.ref_sys_name AS ref_sys_name,
b.is_geographic AS is_geographic, b.has_flipped_axes AS has_flipped_axes, b.spheroid AS spheroid, b.prime_meridian AS prime_meridian, b.datum AS datum, b.projection AS projection, b.unit AS unit,
b.axis_1_name AS axis_1_name, b.axis_1_orientation AS axis_1_orientation,
b.axis_2_name AS axis_2_name, b.axis_2_orientation AS axis_2_orientation,
a.proj4text AS proj4text, a.srtext AS srtext
FROM spatial_ref_sys AS a
LEFT JOIN spatial_ref_sys_aux AS b ON (a.srid = b.srid)
/* spatial_ref_sys_all(srid,auth_name,auth_srid,ref_sys_name,is_geographic,has_flipped_axes,spheroid,prime_meridian,datum,projection,unit,axis_1_name,axis_1_orientation,axis_2_name,axis_2_orientation,proj4text,srtext) */;
CREATE TABLE Observation (    OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   GDB_ID TEXT,   PROJECT TEXT,   PROJECT_NUMBER TEXT,   FUNCTION TEXT,   OBSERVED_BY TEXT,   DATE_OBSERVED TEXT,   POSITIONING_METHOD INTEGER,   RELIABILITY INTEGER,   OBSID TEXT,   LOCATION TEXT,   O_TYPE INTEGER,   LENGTH REAL,   WIDTH REAL,   STRIKE INTEGER,   REMARKS TEXT,   O_HEIGHT REAL,   LAT REAL,   LON REAL, "geometry" POINT, O_TYPE_TEXT TEXT);
CREATE TABLE Sample (    OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   GDB_ID TEXT,   PROJECT TEXT,   PROJECT_NUMBER TEXT,   FUNCTION TEXT,   OBSERVED_BY TEXT,   DATE_OBSERVED TEXT,   POSITIONING_METHOD INTEGER,   RELIABILITY INTEGER,   BO_GID TEXT,   OBSID TEXT,   SAMPLEID TEXT,   C_ANALYSIS INTEGER,   THIN_SECTION INTEGER,   ROCK_NAME INTEGER,   FIELD_NAME TEXT,   LAT REAL,   LON REAL, "geometry" POINT, ROCK_NAME_TEXT TEXT, C_ANALYSIS_TEXT TEXT, THIN_SECTION_TEXT TEXT);
CREATE TABLE Outcrop_picture (    OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   GDB_ID TEXT,   PROJECT TEXT,   PROJECT_NUMBER TEXT,   FUNCTION TEXT,   OBSERVED_BY TEXT,   DATE_OBSERVED TEXT,   POSITIONING_METHOD INTEGER,   RELIABILITY INTEGER,   BO_GID TEXT,   OBSID TEXT,   PICTURE_ID TEXT,   P_DATE TEXT,   TYPE INTEGER,   REMARKS TEXT,   LAT REAL,   LON REAL, "geometry" POINT, TYPE_TEXT TEXT);
CREATE TABLE Rock_observation_point (    OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   GDB_ID TEXT,   PROJECT TEXT,   PROJECT_NUMBER TEXT,   FUNCTION TEXT,   OBSERVED_BY TEXT,   DATE_OBSERVED TEXT,   POSITIONING_METHOD INTEGER,   RELIABILITY INTEGER,   BO_GID TEXT,   OBSID TEXT,   PERCENTAGE INTEGER,   FIELD_NAME TEXT NOT NULL,   ROCK_CLASS INTEGER,   OCCURRENCE_TYPE INTEGER,   ROCK_NAME INTEGER,   GROUPING_NAME TEXT,   MIN_SUSKEPTIBILITY REAL,   MAX_SUSKEPTIBILITY REAL,   W_COLOR TEXT,   COLOR INTEGER,   COLOR_ATTRIBUTE INTEGER,   REMARKS TEXT,   GRAIN_SIZE INTEGER,   LAT REAL,   LON REAL, "geometry" POINT, ROCK_NAME_TEXT TEXT, ROCK_CLASS_TEXT TEXT, OCCURRENCE_TYPE_TEXT TEXT, COLOR_ATTRIBUTE_TEXT TEXT, COLOR_TEXT TEXT, GRAIN_SIZE_TEXT TEXT);
CREATE TABLE Tectonic_measurement (    OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   GDB_ID TEXT,   PROJECT TEXT,   PROJECT_NUMBER TEXT,   FUNCTION TEXT,   OBSERVED_BY TEXT,   DATE_OBSERVED TEXT,   POSITIONING_METHOD INTEGER,   RELIABILITY INTEGER,   GDB_MOD TEXT,   BO_GID TEXT,   OBSID TEXT,   LAT REAL,   LON REAL, "geometry" POINT);
CREATE TABLE BFDS_Mineral (    OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   GDB_ID TEXT,   GDB_MOD TEXT,   ROP_GID TEXT,   FIELD_NAME TEXT,   M_NAME INTEGER,   NAME_SOURCE INTEGER,   INDEX_MINERAL INTEGER,   MIN_GRAIN_SIZE REAL,   MAX_GRAIN_SIZE REAL,   CRYSTAL_FORM INTEGER,   PERCENTAGE INTEGER,   TEXTURE INTEGER,   COLOR TEXT,   COMPOSITION TEXT,   REMARKS TEXT, TEXTURE_TEXT TEXT, M_NAME_TEXT TEXT, CRYSTAL_FORM_TEXT TEXT);
CREATE TABLE BFDS_MaA (    OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   GDB_ID TEXT,   GDB_MOD TEXT,   ROP_GID TEXT,   ALTERATION INTEGER,   STAGE INTEGER,   M_SIGNS INTEGER,   M_TYPE INTEGER,   REMARKS TEXT, ALTERATION_TEXT TEXT, STAGE_TEXT TEXT, M_SIGNS_TEXT TEXT, M_TYPE_TEXT TEXT);
CREATE TABLE BFDS_SaT (    OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   GDB_ID TEXT,   GDB_MOD TEXT,   ROP_GID TEXT,   ST_1 INTEGER,   ST_2 TEXT,   REMARKS TEXT);
CREATE TABLE BFDS_Mineral_data (    OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   GDB_ID TEXT,   GDB_MOD TEXT,   M_GID TEXT,   APPEARANCE INTEGER,   ATTRIBUTES INTEGER, APPEARANCE_TEXT TEXT);
CREATE TABLE BFDS_Linear_structure (    OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   GDB_ID TEXT,   GDB_MOD TEXT,   TM_GID TEXT,   STYPE INTEGER,   RELATIVE_AGE INTEGER,   AREAL_RELATIVE_AGE INTEGER,   DIRECTION INTEGER,   PLUNGE INTEGER,   TO_MAP INTEGER,   F_AXIS_SIZE INTEGER,   F_TYPE INTEGER,   SENCE_OF_ASYMMETRY INTEGER,   F_WAVELENGTH REAL,   F_CLASSIFICATION INTEGER,   L_TYPE INTEGER,   L_ATTRIBUTE INTEGER,   L_INTENSITY INTEGER,   SZ_CODE INTEGER,   REMARKS TEXT, LAT REAL, LON REAL, STYPE_TEXT TEXT, F_AXIS_SIZE_TEXT TEXT, SENCE_OF_ASYMMETRY_TEXT TEXT, L_TYPE_TEXT TEXT, L_ATTRIBUTE_TEXT TEXT, L_INTENSITY_TEXT TEXT);
CREATE TABLE BFDS_Planar_structure (    OBJECTID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,   GDB_ID TEXT,   GDB_MOD TEXT,   TM_GID TEXT,   STYPE INTEGER,   DIRECTION_OF_DIP INTEGER,   DIP INTEGER,   STRIKE INTEGER,   BEDDING_TYPE INTEGER,   YOUNGING_DIRECTION INTEGER,   BED_THICKNESS REAL,   TO_MAP INTEGER,   FOL_TYPE INTEGER,   RELATIVE_AGE INTEGER,   AREAL_RELATIVE_AGE INTEGER,   FOL_APPEARANCE INTEGER,   FOL_FREQUENCY REAL,   FOL_GRADE INTEGER,   F_TYPE INTEGER,   F_APP1 INTEGER,   H_DISPLACEMENT REAL,   H_SENCE INTEGER,   V_DISPLACEMENT REAL,   V_SENCE INTEGER,   F_ZONE_WIDTH REAL,   F_ABUNDANCE INTEGER,   F_RELATIONSHIP INTEGER,   F_TEXTURE INTEGER,   J_QUALITY INTEGER,   J_F_TYPE INTEGER,   J_F_MATERIAL TEXT,   WATER_APPEARANCE INTEGER,   VEIN_TYPE INTEGER,   VEIN_MATERIAL TEXT,   VEIN_WIDTH REAL,   VEIN_LENGTH REAL,   C_CLASS INTEGER,   C_TYPE INTEGER,   C_NAME1 TEXT,   C_NAME2 TEXT,   C_APPEARANCE INTEGER,   J_APERTURE REAL,   J_SPECIAL_TYPE INTEGER,   ALTERATION_WIDTH REAL,   J_LENGTH REAL,   J_SHAPE INTEGER,   J_ROUGHNESS INTEGER,   J_ROUGHNESS_NUMBER REAL,   J_ALTERATION INTEGER,   J_ALTERATION_NUMBER REAL,   J_CONTINUITY INTEGER,   SZ_CODE INTEGER,   REMARKS TEXT, LAT REAL, LON REAL, STYPE_TEXT TEXT, BEDDING_TYPE_TEXT TEXT, FOL_TYPE_TEXT TEXT, H_SENCE_TEXT TEXT, FOL_GRADE_TEXT TEXT, RELATIVE_AGE_TEXT TEXT);
