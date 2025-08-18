create database Foodwastedb

use Foodwastedb

CREATE TABLE Providers (
    Provider_ID INT ,
    Name VARCHAR(100) ,
    Type VARCHAR(50) ,
    Address VARCHAR(255) ,
    City VARCHAR(100) ,
    Contact VARCHAR(50) 
);

create table Receivers (
Receiver_ID int,
Name varchar(255),
Type varchar(255),
City Varchar(255),
Contact varchar(255)
);

create table Food_Listings_Dataset(
Food_ID int,
Food_Name varchar(255),
Quantity int,
Expiry_Date Date,
Provider_ID int,
Provider_Type varchar(255),
Location varchar(255),
Food_Type varchar(255),
Meal_Type varchar(255)
);

create table Claims(
CLaim_ID int,
Food_ID int, 
Receiver_Id int,
Status varchar(255),
Timestamp datetime
)

select * from Claims
select * from Receivers
select * from Providers
select* from Food_Listings_Dataset

ALTER TABLE Providers
ALTER COLUMN Contact VARCHAR(50);

