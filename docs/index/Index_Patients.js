[
  { v: 2, key: { _id: 1 }, name: '_id_' },
  {
    v: 2,
    key: {
      'HomeHealthAndDMEDetails.FacilityRef': 1,
      'HomeHealthAndDMEDetails.IsActive': -1
    },
    name: 'IX_Patient_HomeHealth_IsActive_Facility'
  },
  {
    v: 2,
    key: { SubMarketAccessRef: 1, FirstNameLower: 1, LastNameLower: 1 },
    name: 'IX_SubMarket_FNL_LNL'
  },
  {
    v: 2,
    key: {
      'Address.IsActive': -1,
      'Address.AddressTypeId': 1,
      'Address.Zip5': 1
    },
    name: 'IX_Address_IsActive_AddressTypeId_Zip5'
  },
  {
    v: 2,
    key: {
      'OutreachActivitiesList.IsActive': -1,
      'OutreachActivitiesList.FromRef': 1,
      'OutreachActivitiesList.FacilityRef': 1
    },
    name: 'IX_Patient_OutReach_IsActive_Facility'
  },
  { v: 2, key: { 'Pcp.AddressRef': 1 }, name: 'IX_PCP_Address' },
  {
    v: 2,
    key: { HealthPlanCityRef: 1, PreferredLandmarkProvider: 1 },
    name: 'IX_CoverageMap'
  },
  {
    v: 2,
    key: {
      PreferredProviderRef: 1,
      'EpisodeOfCare.IsUrgentEpisodeClosed': 1,
      'EpisodeOfCare.EndDate': 1
    },
    name: 'IX_PreferredProvider_IsUrgentEpisodeClosed_EndDate'
  },
  {
    v: 2,
    key: { SubscriberId: 1, FirstName: 1 },
    name: 'SubscriberId_1_FirstName_1'
  },
  {
    v: 2,
    key: { 'Specialists.SpecialistRef': 1, 'Specialists.IsActive': -1 },
    name: 'IX_PatientSpecialist'
  },
  {
    v: 2,
    key: {
      TimeZone: 1,
      CallBackDateTime: 1,
      OutreachLockedBy: 1,
      IsQueueExcluded: 1,
      EngagedIndicatorRef: 1,
      OPCScore: 1,
      HealthPlanRef: 1,
      HealthPlanCityRef: 1,
      BrandRef: 1,
      SchedulingProviders: 1
    },
    name: 'IX_IV_Queue_Patients'
  },
  {
    v: 2,
    key: { HealthPlanRef: 1, HealthPlanCityRef: 1, ZipCodeForSchedule: 1 },
    name: 'IX_HealthAndZip'
  },
  { v: 2, key: { FirstNameLower: 1 }, name: 'IX_FirstNameLower' },
  {
    v: 2,
    key: { IsQueueExcluded: 1, EngagedIndicatorRef: 1 },
    name: 'IX_IsQueueExcluded_EngagedIndicatorRef'
  },
  {
    v: 2,
    key: {
      EngagedIndicatorRef: 1,
      SubMarketAccessRef: 1,
      AssignedIDTLiaisonRef: 1,
      CarePlanActiveSection: 1
    },
    name: 'EngagedIndicatorRef_1_SubMarketAccessRef_1_AssignedIDTLiaisonRef_1_CarePlanActiveSection_1'
  },
  {
    v: 2,
    key: { EngagedIndicatorRef: 1, BrandRef: 1 },
    name: 'IX_IV_MV_Queue_Exclusion_Patients_BrandMaster'
  },
  {
    v: 2,
    key: { EngagedIndicatorRef: 1 },
    name: 'IX_Patients_EngagedIndicatorRef'
  },
  { v: 2, key: { PODRef: 1 }, name: 'IX_PODRef' },
  {
    v: 2,
    key: { IsUpdatedByProcess: -1 },
    name: 'IsUpdatedByProcess_-1'
  },
  {
    v: 2,
    key: { PreferredLandmarkProvider: 1, _id: 1 },
    name: 'IX_Container_PreferredLandmarkProvider_id'
  },
  {
    v: 2,
    key: {
      HealthPlanCityRef: 1,
      HealthPlanRef: 1,
      'SchedulingProviders.0': 1
    },
    name: 'HealthPlanCityRef_1_HealthPlanRef_1_SchedulingProviders.0_1'
  },
  { v: 2, key: { OutreachLockedBy: 1 }, name: 'IX_OutreachLockedBy' },
  {
    v: 2,
    key: { CancelAppointmentsDueToPatientDeceased: -1 },
    name: 'IX_Patients_CancelAppointmentsDueToPatientDeceased'
  },
  {
    v: 2,
    key: { 'DocuSign.DocuSignStatus': 1, 'DocuSign.DownloadStatus': 1 },
    name: 'IX_Patients_DocuSign_DocuSignStatus_DownloadStatus'
  },
  {
    v: 2,
    key: {
      EngagedIndicatorRef: -1,
      CarePlanActiveSection: 1,
      NurseCareManagerRef: 1,
      PreferredProviderRef: 1,
      SubMarketAccessRef: 1
    },
    name: 'IX_CarePlanMetrics_Index'
  },
  {
    v: 2,
    key: {
      CareCoordinatorRef: 1,
      'EpisodeOfCare.IsUrgentEpisodeClosed': 1,
      'EpisodeOfCare.EndDate': 1
    },
    name: 'IX_CC_IsUrgentEpisodeClosed_EndDate'
  },
  {
    v: 2,
    key: {
      PreferredLandmarkProvider: 1,
      SubMarketAccessRef: 1,
      EnrolledInd: -1,
      IsQueueExcluded: 1,
      MVScore: 1,
      OutreachLockedBy: 1,
      TimeZone: 1,
      LocalOutreachQueueActive: 1
    },
    name: 'IX_PatientsMVQueue'
  },
  { v: 2, key: { 'Misc.Section': 1 }, name: 'IX_Misc_Section' },
  {
    v: 2,
    key: { 'PatientCallLog.CreatedByRef': 1, 'PatientCallLog.CreatedOn': 1 },
    name: 'IX_PatientCallLog'
  },
  {
    v: 2,
    key: { 'CaseData.UpdatedOn': -1 },
    name: 'CaseData.UpdatedOn_-1'
  },
  {
    v: 2,
    key: { HealthPlanRef: 1, HealthPlanCityRef: 1, SubscriberId: 1 },
    name: 'IX_SubId_HealthPlanRef_HealthPlanCityRef'
  },
  {
    v: 2,
    key: {
      EngagedIndicatorRef: 1,
      ZipCodeForSchedule: 1,
      HealthPlanRef: 1,
      HealthPlanCityRef: 1
    },
    name: 'IX_Scheduling_Providers_Update'
  },
  {
    v: 2,
    key: { OutreachLockedTime: 1 },
    name: 'IX_OutreachLockedTime'
  },
  {
    v: 2,
    key: {
      SchedulingProviders: 1,
      IsQueueExcluded: 1,
      EngagedIndicatorRef: 1,
      EnrolledInd: -1,
      SubMarketAccessRef: 1,
      OutreachLockedBy: 1,
      OPCScore: 1,
      CallBackDateTime: -1
    },
    name: 'IX_SchedulingProviders_OutreachLockedBy_IsQueueExcl_EngagedIndRef_EnrolledInd'
  },
  {
    v: 2,
    key: {
      NurseCareManagerRef: 1,
      'EpisodeOfCare.IsUrgentEpisodeClosed': 1,
      'EpisodeOfCare.EndDate': 1
    },
    name: 'IX_NCM_IsUrgentEpisodeClosed_EndDate'
  },
  { v: 2, key: { BrandRef: -1 }, name: 'IX_BrandRef' },
  {
    v: 2,
    key: { Dob: 1, FirstName: 1, MiddleName: 1, LastName: 1 },
    name: 'IX_Patients_Dob_FN_MN_LN'
  },
  {
    v: 2,
    key: { 'Pcp.PcpRef': -1, 'Pcp.PcpId': -1 },
    name: 'Pcp.PcpRef_-1_Pcp.PcpId_-1'
  },
  {
    v: 2,
    key: {
      PatientId: 1,
      MobileAppRegistration: 1,
      'MobileAppRegistration.PhoneNumber': 1
    },
    name: 'IX_MobileAppRegistrationPhoneCheck'
  },
  {
    v: 2,
    key: {
      AmbassadorRef: 1,
      'EpisodeOfCare.IsUrgentEpisodeClosed': 1,
      'EpisodeOfCare.EndDate': 1
    },
    name: 'IX_Ambassador_IsUrgentEpisodeClosed_EndDate'
  },
  {
    v: 2,
    key: { PatientId: 1, FirstName: 1, MiddleName: 1, LastName: 1 },
    name: 'IX_Patients_PatiendId_FN_MN_LN'
  },
  {
    v: 2,
    key: {
      LocalOutreachQueueActive: -1,
      LocalOutreachOwner: -1,
      CallBackDateTime: -1
    },
    name: 'IX_PatientsLocalOutReachTodayList'
  },
  {
    v: 2,
    key: {
      'SubscribedUserDetails.UserName': 1,
      'SubscribedUserDetails.IsActive': -1,
      'SubscribedUserDetails.IsReceived': 1,
      PatientId: 1
    },
    name: 'IX_SubscribedUserDetails'
  },
  {
    v: 2,
    key: { PreferredProviderRef: 1, PODRef: 1, NurseCareManagerRef: 1 },
    name: 'IX_IDTAssignment'
  },
  {
    v: 2,
    key: {
      'EpisodeOfCare.IsUrgentEpisodeClosed': -1,
      'EpisodeOfCare.EndDate': 1,
      SubMarketAccessRef: 1
    },
    name: 'IX_EpisodeOfCare_EndDate_SubMarketAccessRef'
  },
  {
    v: 2,
    key: {
      EngagedIndicatorRef: 1,
      IsQueueExcluded: 1,
      EnrolledInd: 1,
      CurrentCaseType: 1,
      OutreachCallDate: 1,
      LoadToQueueDate: 1,
      LocalOutreachQueueActive: -1,
      OutreachStatusRef: 1,
      'Phones.IsActive': -1,
      'Phones.MemberPhoneStatus': 1
    },
    name: 'IX_IV_Queue_Exclusion_Patients',
    background: true
  },
  {
    v: 2,
    key: { UpdatedOn: 1 },
    name: 'IX_UpdatedOn',
    background: true
  },
  {
    v: 2,
    key: { 'PatientAcuityIntensityHistory.UpdatedOn': 1 },
    name: 'IX_PatientAcuityIntensityHistory_UpdatedOn',
    background: true,
    hidden: true
  },
  {
    v: 2,
    key: { 'Misc.UpdatedOn': -1 },
    name: 'IX_Misc_UpdatedOn',
    background: true,
    hidden: true
  },
  { v: 2, key: { MedicareId: 1 }, name: 'MedicareId_1' },
  {
    v: 2,
    key: { RecordLastModifiedByRef: 1, RecordLastModifiedUTC: 1, _id: 1 },
    name: 'IX_RecordByRef_UTC_id'
  },
  {
    v: 2,
    key: { RecordLastModifiedUTC: 1, _id: 1 },
    name: 'IX_RecordLastModifiedUTC_id'
  },
  {
    v: 2,
    key: { EngagedIndicatorRef: 1, MedicareId: 1, EnrolledInd: 1 },
    name: 'IX_EngagedIndicatorRef_MedicareId_EnrolledInd'
  },
  {
    v: 2,
    key: { IsPalliativeProcessed: 1 },
    name: 'IX_IsPalliativeProcessed'
  },
  {
    v: 2,
    key: { 'Pcp.PcpRef': 1, 'Pcp.UpdatedOn': 1, 'Pcp.AddressRef': 1 },
    name: 'IX_Pcp.PcpRef_UpdatedOn_AddressRef'
  },
  {
    v: 2,
    key: { SubscribedUserDetails: 1 },
    name: 'IX_SubscribedUserDetails_root'
  },
  { v: 2, key: { Intensity: 1 }, name: 'IX_Intensity' },
  {
    v: 2,
    key: { 'CaseData._id': 1, CaseData: 1 },
    name: 'IX_CaseData._id_CaseData'
  },
  { v: 2, key: { GoldenId: 1 }, name: 'IX_GoldenId', background: true },
  {
    v: 2,
    key: {
      'Address.StateCode': 1,
      'Address.AddressTypeValue': 1,
      HealthPlanName: 1,
      EnrolledInd: 1
    },
    name: 'IX_CPM_AddressStateCode',
    background: true
  },
  {
    v: 2,
    key: { PatientId: 1, AthenaPatientId: 1 },
    name: 'IX_PatientId_AthenaPatientId',
    background: true
  },
  {
    v: 2,
    key: { AthenaPatientId: 1, EnrolledInd: 1 },
    name: 'IX_AthenaPatientId',
    background: true
  }
]
