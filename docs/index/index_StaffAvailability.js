[
    {
      v: 2,
      key: { StaffRef: 1, AvailabilityDate: 1 },
      name: 'StaffRef_1_AvailabilityDate_1'
    },
    { v: 2, key: { StaffUserName: 1 }, name: 'StaffUserName' },
    {
      v: 2,
      key: {
        StaffUserName: 1,
        'Slots.Appointments.AppointmentTypeRef': -1,
        UpdatedOn: -1
      },
      name: 'IX_StaffUserName_ApptRef_UpdatedOn'
    },
    {
      v: 2,
      key: {
        StaffUserName: 1,
        'Slots.Appointments.AppointmentTypeRef': -1,
        'Slots.Appointments.UpdatedOn': -1
      },
      name: 'IX_StaffUserName_ApptRef_Appt_UpdatedOn'
    },
    {
      v: 2,
      key: {
        'Slots.Appointments.PalliativeCoVisitAppointmentRef': 1,
        IsActive: -1
      },
      name: 'IX_PalliativeCoVisitAppointmentRef'
    },
    {
      v: 2,
      key: {
        StaffUserName: 1,
        LastModifiedBy: 1,
        UPDFlag: 1,
        'Slots.Appointments.PatientRef': 1
      },
      name: 'IX_ServerToClient_Sync'
    },
    {
      v: 2,
      key: { StaffUserName: -1, IsActive: -1 },
      name: 'IX_StaffAvailabilitySchedulingOutToDate'
    },
    { v: 2, key: { UPDFlag: 1 }, name: 'IX_UPDFlag' },
    {
      v: 2,
      key: { StaffUserName: 1, 'Slots.UpdatedOn': -1 },
      name: 'IX_StaffUserName_Slots_UpdatedOn'
    },
    {
      v: 2,
      key: {
        IsActive: -1,
        AvailabilityDate: 1,
        IsAvailableForIVQueue: -1,
        IVtoScheduleAvailable: 1,
        'Slots.SlotStatusRef': 1,
        'Slots.IsExceptionSlot': 1,
        'Slots.ISAvailableForIVQueue': -1,
        StaffUserName: 1
      },
      name: 'IX_IsActive_AvailabilityDate_IsExceptionSlot'
    },
    {
      v: 2,
      key: {
        AvailabilityDate: 1,
        'Slots.Appointments.SubMarketAccessRef': 1,
        'Slots.Appointments.PatientPodRef': 1,
        'Slots.IsExceptionSlot': 1
      },
      name: 'IX_Exception_Management'
    },
    { v: 2, key: { IsActive: -1 }, name: 'IX_IsActive' },
    {
      v: 2,
      key: { IsActive: -1, StaffRef: -1, AvailabilityDate: -1 },
      name: 'IX_StaffAvailabilityViewAvailabilityList'
    },
    {
      v: 2,
      key: {
        IsActive: 1,
        AvailabilityDate: 1,
        'Slots.Appointments.VisitStatusRef': 1
      },
      name: 'IX_IV_Queue_Exclusion_StaffAvailability'
    },
    {
      v: 2,
      key: { IsActive: 1, IVLockedOn: -1 },
      name: 'IX_LockRelease_IVLockedOn'
    },
    {
      v: 2,
      key: { 'Slots.Appointments.PatientRef': 1 },
      name: 'PatientRef'
    },
    {
      v: 2,
      key: { 'Slots.Appointments.UpdatedOn': -1 },
      name: 'IX_Appointments_UpdatedOn'
    },
    {
      v: 2,
      key: {
        IsActive: 1,
        StaffUserName: 1,
        AvailabilityDate: 1,
        'Slots.Appointments.StatusRef': 1,
        'Slots.Appointments.VisitStatusRef': 1,
        'Slots.Appointments.VisitStartDateTime': 1
      },
      name: 'IX_StaffAvailabilityFirtAppointmentPushNotification'
    },
    { v: 2, key: { IVLockedBy: 1 }, name: 'IX_IVLockedBy' },
    {
      v: 2,
      key: { 'Slots.Appointments.AdminTimeRef': 1, AvailabilityDate: 1 },
      name: 'Slots.Appointments.AdminTimeRef_1_AvailabilityDate_1'
    },
    { v: 2, key: { 'Slots.Appointments._id': 1 }, name: 'Appointments' },
    {
      v: 2,
      key: { StaffUserName: 1, UpdatedOn: -1 },
      name: 'IX_StaffUserName_UpdatedOn'
    },
    {
      v: 2,
      key: {
        StaffUserName: 1,
        'Slots.Appointments.AppointmentTypeRef': -1,
        'Slots.UpdatedOn': -1
      },
      name: 'IX_StaffUserName_ApptRef_Slot_UpdatedOn'
    },
    {
      v: 2,
      key: {
        IsActive: -1,
        IsAvailableForMVQueue: -1,
        AvailabilityDate: 1,
        'Slots.SlotStatusRef': 1,
        'Slots.IsExceptionSlot': 1,
        'Slots.ISAvailableForMVQueue': -1,
        'Slots.TotalAvailableVisitTime': 1,
        StaffUserName: 1
      },
      name: 'IX_StaffAvailability_MVQueue'
    },
    {
      v: 2,
      key: { StaffUserName: 1, AvailabilityDate: 1, IsActive: 1 },
      name: 'StaffUserName_1_AvailabilityDate_1_IsActive_1',
      unique: true
    },
    { v: 2, key: { 'Slots._id': 1 }, name: 'IX_Slots_id' },
    {
      v: 2,
      key: {
        Zipcodes: 1,
        IsActive: 1,
        IsAvailableForIVQueue: -1,
        IVtoScheduleAvailable: 1,
        AvailabilityDate: 1,
        StaffUserName: 1
      },
      name: 'IX_StaffUserName_IsActive_AvailabilityDate'
    },
    {
      v: 2,
      key: { StaffType: 1, IsActive: 1, AvailabilityDate: 1 },
      name: 'StaffType_1_IsActive_1_AvailabilityDate_1'
    },
    {
      v: 2,
      key: {
        IsActive: 1,
        AvailabilityDate: 1,
        IsAvailableForIVQueue: -1,
        IVtoScheduleAvailable: 1,
        Zipcodes: 1
      },
      name: 'IX_IV_Queue_StaffAvailability'
    },
    {
      v: 2,
      key: { IsActive: -1, AvailabilityDate: -1 },
      name: 'IX_StaffAvailabilityVisitSchedularUVPDVEtcSearch'
    },
    {
      v: 2,
      key: { StaffUserName: 1, 'Slots.Appointments.UpdatedOn': -1 },
      name: 'IX_StaffUserName_Appointments_UpdatedOn'
    },
    { v: 2, key: { UpdatedOn: -1 }, name: 'IX_UpdatedOn' },
    {
      v: 2,
      key: { RecordLastModifiedUTC: -1 },
      name: 'IX_RecordLastModifiedUTC'
    },
    { v: 2, key: { 'Slots.UpdatedOn': -1 }, name: 'IX_Slots_UpdatedOn' },
    {
      v: 2,
      key: {
        IsActive: -1,
        AvailabilityDate: 1,
        'Slots.Appointments.VisitTypeRef': 1,
        'Slots.Appointments.VisitStatusRef': 1
      },
      name: 'IX_IsActive_AvailabilityDate_Appointments'
    },
    { v: 2, key: { AvailabilityDate: 1 }, name: 'AvailabilityDate' },
    {
      v: 2,
      key: { IsActive: 1, LockedOn: -1 },
      name: 'IX_LockRelease_LockedOn'
    },
    {
      v: 2,
      key: { IsActive: -1, LockedBy: 1, LockedFromScreen: 1 },
      name: 'IX_IsActive_LockedBy_LockedFromScreen'
    },
    {
      v: 2,
      key: {
        StaffUserName: 1,
        IsActive: 1,
        IsAvailableForIVQueue: 1,
        AvailabilityDate: 1
      },
      name: 'StaffUserName_1_IsActive_1_IsAvailableForIVQueue_1_AvailabilityDate_1'
    },
    { v: 2, key: { _id: 1 }, name: '_id_' },
    {
      v: 2,
      key: { RecordLastModifiedUTC: 1, _id: 1 },
      name: 'IX_RecordLastModifiedUTC_id'
    },
    {
      v: 2,
      key: { 'Slots.Appointments.UpdatedTimeZone': 1 },
      name: 'Slots.Appointments.UpdatedTimeZone_1'
    },
    {
      v: 2,
      key: { 'Slots.Appointments.CreatedTimeZone': 1 },
      name: 'Slots.Appointments.CreatedTimeZone_1'
    }
  ]