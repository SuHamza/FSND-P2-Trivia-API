import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# Pagination Function
def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_ques = questions[start:end]

  return current_ques

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app)

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 
                          'Content-Type, Authorization, true')
    response.headers.add('Access-Control-Allow-Methods',
                          'GET, PUT, POST, DELETE, OPTIONS')
    return response

  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():
    # Retrieve all categories from DB
    categories = Category.query.order_by(Category.id).all()

    if len(categories) == 0:
      # No questions found!
      abort(404)

    # Format Categories as a Dictionary
    cat_dic = {}
    for cat in categories:
      cat_dic[cat.id] = cat.type

    return jsonify({
      'success': True,
      'categories': cat_dic
    })


  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  def get_questions():
    # Retrieve all questions from DB
    selection = Question.query.order_by(Question.id).all()
    # Retrieve current questions for each page
    current_ques = paginate_questions(request, selection)
    # Retrieve all categories from DB
    categories = Category.query.order_by(Category.id).all()
    # Format Categories as a Dictionary
    cat_dic = {}
    for cat in categories:
      cat_dic[cat.id] = cat.type

    if len(current_ques) == 0:
      # No questions found!
      abort(404)

    return jsonify({
      'success': True,
      'questions': current_ques,
      'total_questions': len(Question.query.all()),
      'categories': cat_dic
    })

  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:ques_id>', methods=['DELETE'])
  def delete_question(ques_id):
    try:
      question = Question.query.filter(Question.id == ques_id).one_or_none()

      if question is None:
        # Question Not Found!
        abort(404)

      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_ques = paginate_questions(request, selection)
      
      return jsonify({
        'success': True,
        'deleted': ques_id,
        'questions': current_ques,
        'total_questions': len(Question.query.all())
        })

    except:
      abort(422)

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def create_ques():
    body = request.get_json()
    
    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_difficulty = body.get('difficulty', None)
    new_category = body.get('category', None)

    try:
      question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
      question.insert()

      selection = Question.query.order_by(Question.id).all()
      current_ques = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'created': question.id,
        'questions': current_ques,
        'total_questions': len(Question.query.all())
      })

    except:
      abort(422)


  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions/search', methods=['POST'])
  def search_ques():
    body = request.get_json()
    searchTerm = body.get('searchTerm', None)

    try:
      selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(searchTerm)))
      current_ques = paginate_questions(request, selection)
      app.logger.info(len(selection.all()))
      return jsonify({
        'success': True,
        'questions': current_ques,
        'total_questions': len(selection.all())
      })
    except:
      abort(422)


  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:cat_id>/questions')
  def get_ques_by_cat(cat_id):
    try:
      selection = Question.query.filter(Question.category == cat_id).all()
      
      # if selection is None:
      #   # No Questions Found!
      #   abort(404)
      
      current_ques = paginate_questions(request, selection)

      if len(current_ques) == 0:
        # No Questions Found!
        abort(404)
      
      return jsonify({
        'success': True,
        'questions': current_ques,
        'total_questions': len(selection),
        'current_category': cat_id
      })
    
    except:
      abort(422)


  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def play_quizz():
    body = request.get_json()

    prev_ques = body.get('previous_questions', None)
    quiz_category = body.get('quiz_category', None)

    try:
      if not quiz_category['id']:
        # If No Category selected
        # Retrieve all questions from DB
        selection = Question.query.all()

      else:
        # Retrieve only questions for selected category
        selection = Question.query.filter(Question.category == quiz_category['id']).all()
      
      app.logger.info(selection)
      if selection is None:
        # No Questions Found!
        abort(404)
      
      # Select a random question by category
      question = random.choice([ques for ques in selection if ques.format() not in prev_ques])

      # if not prev_ques:
      #   # Select a random question by category
      #   question = random.choice(selection)
      #   app.logger.info(question)

      # else:
      #   question = random.choice([ques for ques in selection if ques.format() not in prev_ques])
      #   app.logger.info(question)
        
      return jsonify({
        'success': True,
        'question': question.format()
      })
      
    except:
      abort(422)


  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': 'Resource not found!'
    }), 404
      
  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success': False,
      'error': 422,
      'message': 'Unprocessable Request!'
    }), 422
    
  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'success': False,
      'error': 400,
      'message': 'Bad Request!'
    }), 400
    
  @app.errorhandler(405)
  def not_allowed(error):
    return jsonify({
      'success': False,
      'error': 405,
      'message': 'Method not allowed!'
    }), 405

  return app

    