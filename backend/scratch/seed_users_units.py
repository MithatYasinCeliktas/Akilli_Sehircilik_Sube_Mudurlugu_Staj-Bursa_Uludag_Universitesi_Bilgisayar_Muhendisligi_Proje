import asyncio
import os
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.unit import Unit
from app.core.security import get_password_hash

async def seed_users():
    async with AsyncSessionLocal() as session:
        # Get all units
        res = await session.execute(select(Unit))
        units = res.scalars().all()
        
        unit_dict = {u.id: u for u in units}
        manager_dict = {} # unit_id -> user_id of the manager

        md_content = "# Sistem Kullanıcıları Listesi\n\n"
        
        users_to_add = []
        user_counter = 1
        
        # We need to process units in a way that allows us to link parent managers
        # Since we create 1 manager and 3 users per unit, we can just create them all.
        
        # Step 1: Create all managers first to establish hierarchy
        for u in units:
            manager = User(
                email=f"manager{u.id}@bursa.bel.tr",
                full_name=f"{u.name} Yöneticisi",
                hashed_password=get_password_hash("Bursa123!"),
                role=UserRole.MANAGER,
                unit_id=u.id,
                title="Birim Yöneticisi"
            )
            session.add(manager)
            users_to_add.append(manager)
            
        await session.commit()
        
        # Reload to get manager IDs
        res = await session.execute(select(User).where(User.role == UserRole.MANAGER, User.unit_id.isnot(None)))
        all_managers = res.scalars().all()
        manager_dict = {m.unit_id: m for m in all_managers}
        
        # Step 2: Establish manager_id hierarchy for managers themselves
        for m in all_managers:
            unit = unit_dict[m.unit_id]
            if unit.parent_id and unit.parent_id in manager_dict:
                m.manager_id = manager_dict[unit.parent_id].id
                
        await session.commit()
        
        # Step 3: Create users for each unit
        users_created = []
        for u in units:
            md_content += f"## {u.name} (Birim Tipi: {u.unit_type.value})\n"
            m = manager_dict[u.id]
            md_content += f"- **Yönetici:** {m.full_name} ({m.email}) - Şifre: Bursa123!\n"
            
            for i in range(1, 4):
                user = User(
                    email=f"personel{user_counter}@bursa.bel.tr",
                    full_name=f"Personel {user_counter}",
                    hashed_password=get_password_hash("Bursa123!"),
                    role=UserRole.USER,
                    unit_id=u.id,
                    manager_id=m.id,
                    title="Memur"
                )
                session.add(user)
                users_created.append(user)
                md_content += f"  - **Personel:** {user.full_name} ({user.email}) - Şifre: Bursa123!\n"
                user_counter += 1
                
        await session.commit()
        
        # Step 4: Superuser updating (Assign them to a root unit if any, or leave them independent)
        # The user requested: "superuser'lar bu yapıya uygun şekilde güncellensin"
        # We can find all admins and ensure they don't have department/directorate IDs (which are dropped anyway)
        # We can assign them to the root unit (Bursa Büyükşehir Belediyesi)
        root_unit = next((u for u in units if u.parent_id is None), None)
        if root_unit:
            res = await session.execute(select(User).where(User.role == UserRole.ADMIN))
            admins = res.scalars().all()
            md_content += f"\n## Sistem Yöneticileri (ADMIN)\n"
            for admin in admins:
                # Give admins the root unit if they don't have one, but they can't be MANAGER of the unit if the unit already has a manager.
                # Since their role is ADMIN, the unique index on MANAGER won't block them.
                admin.unit_id = root_unit.id
                md_content += f"- **Admin:** {admin.full_name} ({admin.email})\n"
            await session.commit()
            
        with open("C:/Users/mitha/.gemini/antigravity/brain/095955f7-b18a-4655-9f1b-42e2f695e847/users_list.md", "w", encoding="utf-8") as f:
            f.write(md_content)
            
        print("Users seeded and markdown file created.")

if __name__ == "__main__":
    asyncio.run(seed_users())
