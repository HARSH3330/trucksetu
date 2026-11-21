import uuid

from sqlalchemy import text

from _local_release_db import migrated_schema,run_local


def test_real_migrations_23_and_24_preserve_records_and_require_legacy_reverification():
    provider,application,document=uuid.uuid4(),uuid.uuid4(),uuid.uuid4()
    customer,category,driver,shipment,quote,booking,allocation,trip=[uuid.uuid4() for _ in range(8)]
    def before_23(db):
        db.execute(text("INSERT INTO provider_profiles(id,display_name,provider_type,kyc_status,active) VALUES (:id,'NOT A REAL PROVIDER','owner','verified',true)"),{'id':provider})
        db.execute(text("INSERT INTO kyc_applications(id,provider_id,status,legal_name) VALUES (:id,:provider,'verified','NOT A REAL IDENTITY')"),{'id':application,'provider':provider})
        db.execute(text("INSERT INTO kyc_documents(id,application_id,document_type,storage_key,original_filename,content_type,size_bytes,status) VALUES (:id,:application,'pan','kyc/test/fictional-legacy','NOT-A-REAL-ID.pdf','application/pdf',100,'accepted')"),{'id':document,'application':application})
        db.execute(text("INSERT INTO users(id,full_name,email,password_hash) VALUES (:id,'Fictional local actor','migration@example.com','unused')"),{'id':customer})
        db.execute(text("INSERT INTO vehicle_categories(id,name,body_type,min_capacity_tonnes,max_capacity_tonnes) VALUES (:id,'Fictional migration truck','closed',1,5)"),{'id':category})
        db.execute(text("INSERT INTO driver_profiles(id,provider_id,full_name,masked_mobile,licence_number,kyc_status,active) VALUES (:id,:provider,'Fictional driver','NOT REAL','NOT-REAL-LICENCE','verified',true)"),{'id':driver,'provider':provider})
        db.execute(text("INSERT INTO transport_requests(id,customer_id,public_id,pickup_address,pickup_city,destination_address,destination_city,pickup_date) VALUES (:id,:customer,'TEST-MIGRATION','Fictional pickup','Delhi','Fictional drop','Noida',CURRENT_DATE)"),{'id':shipment,'customer':customer})
        db.execute(text("INSERT INTO quotes(id,request_id,provider_id,vehicle_category_id,final_price,vehicles_offered,estimated_pickup,estimated_delivery) VALUES (:id,:request,:provider,:category,750,1,now(),now())"),{'id':quote,'request':shipment,'provider':provider,'category':category})
        db.execute(text("INSERT INTO bookings(id,request_id,customer_id,public_id,total_amount,customer_snapshot,route_snapshot,cargo_snapshot) VALUES (:id,:request,:customer,'TEST-BOOKING',750,'{}','{}','{}')"),{'id':booking,'request':shipment,'customer':customer})
        db.execute(text("INSERT INTO booking_allocations(id,booking_id,quote_id,provider_id,trucks_allocated,agreed_amount,quote_snapshot) VALUES (:id,:booking,:quote,:provider,1,750,'{}')"),{'id':allocation,'booking':booking,'quote':quote,'provider':provider})
        db.execute(text("INSERT INTO trips(id,allocation_id,driver_id,status) VALUES (:id,:allocation,:driver,'in_transit')"),{'id':trip,'allocation':allocation,'driver':driver})
    async def exercise():
        async with migrated_schema(before_23) as (engine,_):
            async with engine.connect() as db:
                assert (await db.execute(text('SELECT kyc_status,active FROM provider_profiles WHERE id=:id'),{'id':provider})).one()==('resubmit_required',True)
                assert (await db.execute(text('SELECT status FROM kyc_applications WHERE id=:id'),{'id':application})).scalar_one()=='resubmit_required'
                assert (await db.execute(text('SELECT status,storage_version_id FROM kyc_documents WHERE id=:id'),{'id':document})).one()==('rejected',None)
                assert (await db.execute(text("SELECT count(*) FROM audit_logs WHERE action='kyc.version_reverification_required' AND entity_id=:id"),{'id':provider})).scalar_one()==1
                assert (await db.execute(text("SELECT count(*) FROM information_schema.columns WHERE table_schema=current_schema() AND ((table_name='bookings' AND column_name='acceptance_key') OR (table_name='quote_versions' AND column_name='snapshot'))"))).scalar_one()==2
                assert (await db.execute(text('SELECT count(*) FROM provider_profiles'))).scalar_one()==1
                assert (await db.execute(text('SELECT driver_id,status FROM trips WHERE id=:id'),{'id':trip})).one()==(driver,'in_transit')
                assert (await db.execute(text('SELECT kyc_status,active FROM driver_profiles WHERE id=:id'),{'id':driver})).one()==('verified',True)
                assert (await db.execute(text('SELECT total_amount FROM bookings WHERE id=:id'),{'id':booking})).scalar_one()==750
    run_local(exercise())
