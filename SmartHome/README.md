This function set is an API exercise using smart home as an example 
We will use CRUD methodology and object based implementation 
    Create
    Read
    Update
    Delete 


We will want to use JSON based outputs as well as efficient translations and solid unit tests. 
Eventually, it would be good to adjust this into REST APIs as well. 

Assume all devices read in a fixed time frame, no DDOS doorways, no need to over sample
Objects will need hashes

Objects:
House 
Room 
Device 
User 

Functions: 
    Create 
    Read 
    Update 
    Delete 

Attribute examples: 
	Name
	Address 
	Floor 
	Etc
    Permissions levels / users  

Have Unit Tests 

Format will be user based
    1: create user 
    2: as admin user:
        create home 
        add room
        delete floor etc
        etc 
        ... add user
    3: As user or admin user
        read 

format will be key, value based 
