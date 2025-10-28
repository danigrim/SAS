/******************************************************************************
 * Program: demographics_summary.sas
 * Purpose: Simple demographic summary statistics by treatment group
 * Description: Calculates subject count and mean age by treatment arm
 *              This is a demonstration program for SAS-to-Python migration
 * Input: ADSL dataset (Subject-Level Analysis Dataset)
 * Output: Summary statistics table
 ******************************************************************************/

* Set library references;
LIBNAME adam "../../data/adam";

* Calculate summary statistics by treatment group;
PROC MEANS DATA=adam.adsl N MEAN STD MIN MAX MAXDEC=2;
    CLASS trt01p;
    VAR age;
    TITLE "Demographic Summary: Age by Treatment Group";
RUN;

* Count subjects by treatment and sex;
PROC FREQ DATA=adam.adsl;
    TABLES trt01p*sex / NOCOL NOPERCENT;
    TITLE "Subject Count by Treatment and Sex";
RUN;

* Clean up;
LIBNAME adam CLEAR;
