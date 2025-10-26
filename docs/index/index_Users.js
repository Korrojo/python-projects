{
	"name": "_id_",
	"key": {
		"_id": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "337372 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"_id": 1
			},
			"name": "_id_"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IsActive_1_LastName_1",
	"key": {
		"IsActive": 1,
		"LastName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "566 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"IsActive": 1,
				"LastName": 1
			},
			"name": "IsActive_1_LastName_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IsActive_1_FirastName_1_LastName_1",
	"key": {
		"IsActive": 1,
		"FirastName": 1,
		"LastName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "0 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"IsActive": 1,
				"FirastName": 1,
				"LastName": 1
			},
			"name": "IsActive_1_FirastName_1_LastName_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IsActive_1_FirstName_1",
	"key": {
		"IsActive": 1,
		"FirstName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "64 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"IsActive": 1,
				"FirstName": 1
			},
			"name": "IsActive_1_FirstName_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_Manager",
	"key": {
		"Manager": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "1207 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"Manager": 1
			},
			"name": "IX_Manager"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_OptumUserName_IsActive_IsOnlineUser",
	"key": {
		"OptumUserName": 1,
		"IsActive": 1,
		"IsOnlineUser": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "1475 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"OptumUserName": 1,
				"IsActive": 1,
				"IsOnlineUser": 1
			},
			"name": "IX_OptumUserName_IsActive_IsOnlineUser"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_OnlineUser_RoleName",
	"key": {
		"IsOnlineUser": 1,
		"Roles.RoleName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "0 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"IsOnlineUser": 1,
				"Roles.RoleName": 1
			},
			"name": "IX_OnlineUser_RoleName"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_IsActive_SubMarket_Start_EndDate_FirstName_LastName",
	"key": {
		"IsActive": -1,
		"POD.SubMarketAccessRef": 1,
		"POD.StartDate": 1,
		"POD.EndDate": 1,
		"POD.IsActive": -1,
		"FirstName": 1,
		"LastName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "1452 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"IsActive": -1,
				"POD.SubMarketAccessRef": 1,
				"POD.StartDate": 1,
				"POD.EndDate": 1,
				"POD.IsActive": -1,
				"FirstName": 1,
				"LastName": 1
			},
			"name": "IX_IsActive_SubMarket_Start_EndDate_FirstName_LastName"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "ApplicationVersion_1",
	"key": {
		"ApplicationVersion": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "1 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"ApplicationVersion": 1
			},
			"name": "ApplicationVersion_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_PODMatchMDProvider_Users_Search",
	"key": {
		"CredentialRef": 1,
		"Roles.RoleName": 1,
		"IsActive": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "1 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"CredentialRef": 1,
				"Roles.RoleName": 1,
				"IsActive": 1
			},
			"name": "IX_PODMatchMDProvider_Users_Search"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "DirectEmail_1",
	"key": {
		"DirectEmail": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "0 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"DirectEmail": 1
			},
			"name": "DirectEmail_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_UserName_IsActive_RoleName",
	"key": {
		"IsActive": -1,
		"UserName": 1,
		"Roles.RoleName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "1667 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"IsActive": -1,
				"UserName": 1,
				"Roles.RoleName": 1
			},
			"name": "IX_UserName_IsActive_RoleName"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_CredentialRef_FacilityRef_ChartReviewPercentage",
	"key": {
		"CredentialRef": -1,
		"CoSignStaff.FacilityRef": 1,
		"CoSignStaff.ChartReviewRequirementsPercentage": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "0 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"CredentialRef": -1,
				"CoSignStaff.FacilityRef": 1,
				"CoSignStaff.ChartReviewRequirementsPercentage": 1
			},
			"name": "IX_CredentialRef_FacilityRef_ChartReviewPercentage"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_CredentialRef_RoleName_FirstName_LastName",
	"key": {
		"CredentialRef": 1,
		"IsActive": -1,
		"Roles.RoleName": 1,
		"FirstName": 1,
		"LastName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "0 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"CredentialRef": 1,
				"IsActive": -1,
				"Roles.RoleName": 1,
				"FirstName": 1,
				"LastName": 1
			},
			"name": "IX_CredentialRef_RoleName_FirstName_LastName"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "UserName_1",
	"key": {
		"UserName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "83554 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"UserName": 1
			},
			"name": "UserName_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "Permissions.PermissionKey_1_FirstName_1",
	"key": {
		"Permissions.PermissionKey": 1,
		"FirstName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "0 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"Permissions.PermissionKey": 1,
				"FirstName": 1
			},
			"name": "Permissions.PermissionKey_1_FirstName_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_RecordLastModifiedUTC",
	"key": {
		"RecordLastModifiedUTC": -1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "0 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"RecordLastModifiedUTC": -1
			},
			"name": "IX_RecordLastModifiedUTC"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_IsActive_LastLoggedInDate",
	"key": {
		"IsActive": 1,
		"LastLoggedIn": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "0 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"IsActive": 1,
				"LastLoggedIn": 1
			},
			"name": "IX_IsActive_LastLoggedInDate"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_SubMarket_Start_EndDate_FirstName_LastName",
	"key": {
		"POD.SubMarketAccessRef": 1,
		"POD.StartDate": 1,
		"POD.EndDate": 1,
		"POD.IsActive": -1,
		"FirstName": 1,
		"LastName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "2 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"POD.SubMarketAccessRef": 1,
				"POD.StartDate": 1,
				"POD.EndDate": 1,
				"POD.IsActive": -1,
				"FirstName": 1,
				"LastName": 1
			},
			"name": "IX_SubMarket_Start_EndDate_FirstName_LastName"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "InActivatedDate_1_LastName_1",
	"key": {
		"InActivatedDate": 1,
		"LastName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "243 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"InActivatedDate": 1,
				"LastName": 1
			},
			"name": "InActivatedDate_1_LastName_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "LastName_1",
	"key": {
		"LastName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "3 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"LastName": 1
			},
			"name": "LastName_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_IsActive_CoSignStaffUserName",
	"key": {
		"IsActive": -1,
		"CoSignStaff.CoSignStaffUserName": -1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "5 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"IsActive": -1,
				"CoSignStaff.CoSignStaffUserName": -1
			},
			"name": "IX_IsActive_CoSignStaffUserName"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_FirstAppointmentUsers",
	"key": {
		"UserName": 1,
		"PushNotificationToken": -1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "801 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"UserName": 1,
				"PushNotificationToken": -1
			},
			"name": "IX_FirstAppointmentUsers"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_RoleName",
	"key": {
		"Roles.RoleName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "1 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"Roles.RoleName": 1
			},
			"name": "IX_RoleName"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_UserName_POD_HealthPlanCityRef",
	"key": {
		"POD.HealthPlanCityRef": 1,
		"UserName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "0 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"POD.HealthPlanCityRef": 1,
				"UserName": 1
			},
			"name": "IX_UserName_POD_HealthPlanCityRef"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_IsActive_RoleName",
	"key": {
		"IsActive": 1,
		"Roles.RoleName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "51 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"IsActive": 1,
				"Roles.RoleName": 1
			},
			"name": "IX_IsActive_RoleName"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "Roles.RoleName_1_IsActive_1_FirstName_1",
	"key": {
		"Roles.RoleName": 1,
		"IsActive": 1,
		"FirstName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "2 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"Roles.RoleName": 1,
				"IsActive": 1,
				"FirstName": 1
			},
			"name": "Roles.RoleName_1_IsActive_1_FirstName_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "RampStartDate_1_UserName_1",
	"key": {
		"RampStartDate": 1,
		"UserName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "3 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"RampStartDate": 1,
				"UserName": 1
			},
			"name": "RampStartDate_1_UserName_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_Users_Search",
	"key": {
		"IsActive": -1,
		"POD.HealthPlanRef": 1,
		"POD.HealthPlanCityRef": 1,
		"POD.IsActive": -1,
		"POD.StartDate": 1,
		"POD.EndDate": -1,
		"FirstName": 1,
		"LastName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "20 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"IsActive": -1,
				"POD.HealthPlanRef": 1,
				"POD.HealthPlanCityRef": 1,
				"POD.IsActive": -1,
				"POD.StartDate": 1,
				"POD.EndDate": -1,
				"FirstName": 1,
				"LastName": 1
			},
			"name": "IX_Users_Search"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IsActive_1_IsRisk_1_FirastName_1_LastName_1",
	"key": {
		"IsActive": 1,
		"IsRisk": 1,
		"FirastName": 1,
		"LastName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "191 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"IsActive": 1,
				"IsRisk": 1,
				"FirastName": 1,
				"LastName": 1
			},
			"name": "IsActive_1_IsRisk_1_FirastName_1_LastName_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "FirstName_1_LastName_1",
	"key": {
		"FirstName": 1,
		"LastName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "43 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"FirstName": 1,
				"LastName": 1
			},
			"name": "FirstName_1_LastName_1"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
},
{
	"name": "IX_IsActive_UserName",
	"key": {
		"IsActive": -1,
		"UserName": 1
	},
	"type": "REGULAR",
	"ns": "UbiquitySTG3.Users",
	"accesses": "16300 since 7/8/2025, 10:01:14 PM",
	"properties": {
		"spec": {
			"v": 2,
			"key": {
				"IsActive": -1,
				"UserName": 1
			},
			"name": "IX_IsActive_UserName"
		}
	},
	"host": "atlas-pylfl5-shard-00-02.uniwl.mongodb.net:27017"
}