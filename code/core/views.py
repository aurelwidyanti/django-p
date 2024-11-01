from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.shortcuts import render, get_object_or_404
from .models import Course, CourseMember, CourseContent, Comment
from django.db.models import Max, Min, Avg, Count

# Insert User
def insert_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = User.objects.create_user(username=username, email=email, password=password)
        return JsonResponse({"message": "User created", "user_id": user.id})
    return JsonResponse({"error": "Invalid request method"}, status=400)

# Insert Course
def insert_course(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        price = request.POST.get("price")
        teacher_id = request.POST.get("teacher_id")
        teacher = get_object_or_404(User, pk=teacher_id)
        course = Course.objects.create(name=name, description=description, price=price, teacher=teacher)
        return JsonResponse({"message": "Course created", "course_id": course.id})
    return JsonResponse({"error": "Invalid request method"}, status=400)

# Select All Users
def select_all_users(request):
    users = User.objects.all()
    
    if request.method == "GET" and 'html' in request.GET:
        return render(request, 'users.html', {'users': users})

    user_data = [{"id": user.id, "username": user.username, "email": user.email} for user in users]
    return JsonResponse({"users": user_data})

# Select Get by ID
def select_user_by_id(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == "GET" and 'html' in request.GET:
        return render(request, 'user.html', {'user': user})
    
    return JsonResponse({"id": user.id, "username": user.username, "email": user.email})

# Select with Condition
def select_user_by_email(request, email):
    users = User.objects.filter(email=email)
    user_data = [{"id": user.id, "username": user.username, "email": user.email} for user in users]
    return JsonResponse({"users": user_data})

# Update User
def update_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, pk=user_id)
        user.username = request.POST.get("username", user.username)
        user.email = request.POST.get("email", user.email)
        user.save()
        return JsonResponse({"message": "User updated"})
    return JsonResponse({"error": "Invalid request method"}, status=400)

# Delete User
def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.delete()
    return JsonResponse({"message": "User deleted"})

# Delete All Courses
def delete_all_courses(request):
    Course.objects.all().delete()
    return JsonResponse({"message": "All courses deleted"})

# Delete All Users Except Specific IDs
def delete_all_users_except(request):
    if request.method == "POST":
        user_ids = request.POST.getlist("user_ids")
        User.objects.exclude(id__in=user_ids).delete()
        return JsonResponse({"message": "All users except specified deleted"})
    return JsonResponse({"error": "Invalid request method"}, status=400)

def testing(request):
    user_test = User.objects.filter(username="usertesting")
    if not user_test.exists():
        user_test = User.objects.create_user(
                            username="usertesting", 
                            email="usertest@email.com", 
                            password="sanditesting")
    all_users = serializers.serialize('python', User.objects.all())

    admin = User.objects.get(pk=1)
    user_test.delete()

    after_delete = serializers.serialize('python', User.objects.all())

    response = {
            "admin_user": serializers.serialize('python', [admin])[0],
            "all_users" : all_users,
            "after_del" : after_delete,
        }
    return JsonResponse(response)

def all_course(request):
    allCourse = Course.objects.all()
    result = []
    for course in allCourse:
        record = {'id': course.id, 'name': course.name, 
                  'description': course.description, 
                  'price': course.price,
                  'teacher': {
                      'id': course.teacher.id,
                      'username': course.teacher.username,
                      'email': course.teacher.email,
                      'fullname': f"{course.teacher.first_name} {course.teacher.last_name}"
                  }}
        result.append(record)
    return JsonResponse(result, safe=False)

def user_courses(request):
    user = User.objects.get(pk=2)
    courses = Course.objects.filter(teacher=user.id)
    course_data = []
    for course in courses:
        record = {'id': course.id, 'name': course.name, 
                  'description': course.description, 'price': course.price}
        course_data.append(record)
    result = {'id': user.id, 'username': user.username, 'email': user.email, 
              'fullname': f"{user.first_name} {user.last_name}", 
              'courses': course_data}
    return JsonResponse(result, safe=False)

def course_stat(request):
  courses = Course.objects.all()
  stats = courses.aggregate(max_price=Max('price'),
                              min_price=Min('price'),
                              avg_price=Avg('price'))
  cheapest = Course.objects.filter(price=stats['min_price'])
  expensive = Course.objects.filter(price=stats['max_price'])
  popular = Course.objects.annotate(member_count=Count('coursemember'))\
                          .order_by('-member_count')[:5]
  unpopular = Course.objects.annotate(member_count=Count('coursemember'))\
                          .order_by('member_count')[:5]

  result = {'course_count': len(courses), 'courses': stats,
            'cheapest': serializers.serialize('python', cheapest), 
            'expensive': serializers.serialize('python', expensive),
            'popular': serializers.serialize('python', popular), 
            'unpopular': serializers.serialize('python', unpopular)}
  return JsonResponse(result, safe=False)

def course_member_stat(request):
    courses = Course.objects.filter(description__contains='python') \
                            .annotate(member_num=Count('coursemember'))
    course_data = []
    for course in courses:
        record = {'id': course.id, 'name': course.name, 'price': course.price, 
                  'member_count': course.member_num}
        course_data.append(record)
    result = {'data_count': len(course_data), 'data':course_data}
    return JsonResponse(result)

def course_detail(request, course_id):
   course = Course.objects.annotate(member_count=Count('coursemember'), 
                                 content_count=Count('coursecontent'),
                                 comment_count=Count('coursecontent__comment'))\
                           .get(pk=course_id)
   contents = CourseContent.objects.filter(course_id=course.id)\
               .annotate(count_comment=Count('comment'))\
               .order_by('-count_comment')[:3]
   result = {"name": course.name, 'description': course.description, 'price': course.price, 
             'member_count': course.member_count, 'content_count': course.content_count,
             'teacher': {'username': course.teacher.username, 'email': 
                         course.teacher.email, 'fullname': course.teacher.first_name},
             'comment_stat': {'comment_count': course.comment_count, 
                              'most_comment':[{'name': content.name, 
			                               'comment_count': content.count_comment} 
			                               for content in contents]},
             }

   return JsonResponse(result)

def index(request):
    return HttpResponse("<h1>Welcome to Simple LMS</h1>")

def add_data(request):
    course = Course(
        name = "Belajar Django",
        description = "Belajar Django dengan mudah",
        price = 100000,
        teacher = User.objects.get(pk=1)
    )
    course.save()
    return HttpResponse("Data berhasil ditambahkan")

def edit_data(request):
    course = Course.objects.get(pk=1)
    course.name = "Belajar Django dengan mudah"
    course.save()
    return HttpResponse("Data berhasil diubah")

def delete_data(request):
    course = Course.objects.get(pk=1)
    course.delete()
    return HttpResponse("Data berhasil dihapus")

def user_statistics(request):
    non_admin_users = User.objects.exclude(is_superuser=True)
    
    total_non_admin = non_admin_users.count()

    users_with_courses = User.objects.filter(course__isnull=False).distinct().count()

    users_without_courses = total_non_admin - users_with_courses

    avg_courses_followed = CourseMember.objects.values('user_id').annotate(
        course_count=Count('course_id')
    ).aggregate(Avg('course_count'))['course_count__avg']

    top_user = CourseMember.objects.values('user_id').annotate(
        course_count=Count('course_id')
    ).order_by('-course_count').first()
    top_user_info = None
    if top_user:
        user = User.objects.get(pk=top_user['user_id'])
        top_user_info = {"id": user.id, "username": user.username, "course_count": top_user['course_count']}

    users_no_courses = User.objects.exclude(
        id__in=CourseMember.objects.values_list('user_id', flat=True)
    ).values('id', 'username', 'email')

    result = {
        "total_non_admin_users": total_non_admin,
        "users_with_courses": users_with_courses,
        "users_without_courses": users_without_courses,
        "avg_courses_followed": avg_courses_followed,
        "top_user": top_user_info,
        "users_no_courses": list(users_no_courses),
    }
    return JsonResponse(result)

def user_detail_statistics(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    
    courses_followed_count = CourseMember.objects.filter(user_id=user_id).count()
    
    courses_created_count = Course.objects.filter(teacher_id=user_id).count()

    total_course_members = CourseMember.objects.filter(
        course_id__teacher_id=user_id
    ).count()

    comments_posted_count = Comment.objects.filter(member_id__user_id=user_id).count()

    result = {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "fullname": f"{user.first_name} {user.last_name}"
        },
        "courses_followed_count": courses_followed_count,
        "courses_created_count": courses_created_count,
        "total_course_members": total_course_members,
        "comments_posted_count": comments_posted_count,
    }
    return JsonResponse(result)

def user_statistics_html(request):
    # Jumlah user yang membuat course
    users_with_course = User.objects.filter(course__isnull=False).distinct()
    total_users_with_course = users_with_course.count()
    
    # Jumlah user yang tidak memiliki course
    total_users_without_course = User.objects.filter(course__isnull=True).count()
    
    # Rata-rata jumlah course yang diikuti 1 user
    average_courses_per_user = CourseMember.objects.values('user_id').annotate(course_count=Count('course_id')).aggregate(Avg('course_count'))['course_count__avg']
    
    # User yang mengikuti course terbanyak
    top_user = CourseMember.objects.values('user_id').annotate(course_count=Count('course_id')).order_by('-course_count').first()
    top_user_detail = User.objects.get(id=top_user['user_id']) if top_user else None
    top_user_course_count = top_user['course_count'] if top_user else 0
    
    # List user yang tidak mengikuti course sama sekali
    users_without_courses = User.objects.exclude(id__in=CourseMember.objects.values('user_id'))
    
    context = {
        'total_users_with_course': total_users_with_course,
        'total_users_without_course': total_users_without_course,
        'average_courses_per_user': average_courses_per_user,
        'top_user': top_user_detail,
        'top_user_course_count': top_user_course_count,
        'users_without_courses': users_without_courses,
    }
    
    return render(request, 'user-statistics.html', context)