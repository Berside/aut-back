from sqlalchemy import func
from src.db import db
from src.sapr.exceptions import AppError
from src.orm.orm_sapr import AnimationStep, Project
from src.sapr.exceptions import(
    AnimationStepNotFoundError,
    ProjectNotFoundError
)

class AnimationStepService():
    def get_by_project_id(self, project_id: int) -> list[AnimationStep]:
        return AnimationStep.query.filter_by(project_id=project_id).order_by(AnimationStep.order.asc()).all()
    def create_step(
        self,
        project_id: int,
        name: str,
        model_id: int = None,
        duration: float = 1.0,
        order: int = 0,
        is_active: bool = True,
        camera_position: dict = None,
        camera_target: dict = None,
        animation_ids: list = None
    ) -> AnimationStep:
        # Создает шаг анимации
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()

        if order == 0:
            max_order = db.session.query(func.max(AnimationStep.order)).filter_by(
                project_id=project_id
            ).scalar()
            order = (max_order or -1) + 1

        step = AnimationStep(
            project_id=project_id,
            model_id=model_id,
            name=name,
            duration=duration,
            order=order,
            is_active=is_active,
            camera_position=camera_position or {"x": 0, "y": 0, "z": 0},
            camera_target=camera_target or {"x": 0, "y": 0, "z": 0},
            animation_ids=animation_ids or [],
        )
        db.session.add(step)
        db.session.commit()
        return step

    def update_step(self, step_id: int, **kwargs) -> AnimationStep:
        # Обновляет шаг анимации
        step = AnimationStep.query.get(step_id)
        if not step:
            raise AnimationStepNotFoundError()

        for key, val in kwargs.items():
            if val is not None and hasattr(step, key):
                setattr(step, key, val)
        db.session.commit()
        return step

    def delete_step(self, step_id) -> dict:
        # Удаляет шаг анимации
        step = AnimationStep.query.get(step_id)
        if not step:
            raise AnimationStepNotFoundError()

        try:
            db.session.delete(step)
            db.session.commit()
            return {'success': True, 'step_id': step_id}
        except Exception as e:
            db.session.rollback()
            raise AnimationStepNotFoundError(f'Ошибка удаления шага: {str(e)}')

    def delete_all_by_project_id(self, project_id: int) -> dict:
        # Удаляет все шаги анимации для конкретного проекта
        try:
            AnimationStep.query.filter_by(project_id=project_id).delete(synchronize_session=False)
            db.session.commit()
            return {'success': True, 'project_id': project_id}
        except Exception as e:
            db.session.rollback()
            raise AppError(f'Ошибка удаления шагов анимации проекта: {str(e)}')


    def create_steps_bulk(self, project_id: int, steps_data: list) -> list[AnimationStep]:
        # Массовое создание шагов анимации
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()

        created_steps = []
        max_order = db.session.query(func.max(AnimationStep.order)).filter_by(
            project_id=project_id
        ).scalar() or -1

        for item in steps_data:
            order = item.get('order')
            if order is None or order == 0:
                max_order += 1
                order = max_order

            step = AnimationStep(
                project_id=project_id,
                name=item.get('name', 'Новый шаг'),
                model_id=item.get('model_id'),
                duration=float(item.get('duration', 1.0)),
                order=order,
                is_active=item.get('is_active', True),
                camera_position=item.get('camera_position') or {"x": 0.0, "y": 0.0, "z": 0.0},
                camera_target=item.get('camera_target') or {"x": 0.0, "y": 0.0, "z": 0.0},
                animation_ids=item.get('animation_ids', [])
            )
            db.session.add(step)
            created_steps.append(step)
        
        db.session.commit()
        return created_steps

    def search_animation_steps(self, project_id: int, query: str, page: int = 1, per_page: int = 50) -> dict:
        # Поиск шагов анимации по названию в проекте
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()

        if not query or len(query.strip()) < 2:
            return {'steps': [], 'total': 0, 'page': page, 'per_page': per_page}

        search_term = f'%{query.strip()}%'

        stmt = AnimationStep.query.filter(
            AnimationStep.project_id == project_id,
            AnimationStep.name.ilike(search_term)
        )

        total = stmt.count()

        steps = stmt.order_by(AnimationStep.order, AnimationStep.id).offset((page - 1) * per_page).limit(per_page).all()

        return {
            'steps': [
                {
                    'id': step.id,
                    'project_id': step.project_id,
                    'model_id': step.model_id,
                    'name': step.name,
                    'duration': step.duration,
                    'order': step.order,
                    'is_active': step.is_active,
                    'camera_position': step.camera_position,
                    'camera_target': step.camera_target,
                    'animation_ids': step.animation_ids,
                }
                for step in steps
            ],
            'total': total,
            'page': page,
            'per_page': per_page
        }

animation_step_service = AnimationStepService()