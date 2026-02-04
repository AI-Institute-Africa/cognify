"""
LinkedIn Profile Scraping Service using Proxycurl API
Extracts professional data for AI learning personalization
"""
import os
import logging
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

PROXYCURL_API_KEY = os.environ.get('PROXYCURL_API_KEY', '')

class LinkedInScraperService:
    """LinkedIn Profile Scraper using Proxycurl API"""
    
    def __init__(self):
        self.api_key = PROXYCURL_API_KEY
        self.base_url = "https://nubela.co/proxycurl/api/v2"
    
    async def scrape_profile(self, linkedin_url: str) -> Dict[str, Any]:
        """
        Scrape a LinkedIn profile and extract professional data
        Returns structured data for AI learning personalization
        """
        if not self.api_key:
            logger.warning("Proxycurl API key not configured, using AI inference fallback")
            return await self._ai_fallback_analysis(linkedin_url)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/linkedin",
                    params={"url": linkedin_url},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._transform_profile_data(data)
                elif response.status_code == 404:
                    return {"success": False, "error": "LinkedIn profile not found"}
                elif response.status_code == 401:
                    logger.error("Proxycurl API key invalid")
                    return await self._ai_fallback_analysis(linkedin_url)
                else:
                    logger.error(f"Proxycurl API error: {response.status_code}")
                    return await self._ai_fallback_analysis(linkedin_url)
                    
        except Exception as e:
            logger.error(f"LinkedIn scraping error: {e}")
            return await self._ai_fallback_analysis(linkedin_url)
    
    def _transform_profile_data(self, raw_data: Dict) -> Dict[str, Any]:
        """Transform raw Proxycurl data into learner profile format"""
        # Extract skills
        skills = []
        if raw_data.get('skills'):
            skills = [s for s in raw_data['skills'][:10]]
        
        # Extract experience for career insights
        experiences = raw_data.get('experiences', [])
        current_role = experiences[0] if experiences else {}
        
        # Extract education
        education = raw_data.get('education', [])
        highest_education = education[0] if education else {}
        
        # Build strengths from skills and headline
        headline = raw_data.get('headline', '')
        strengths = skills[:5] if skills else []
        if headline and len(strengths) < 5:
            # Add keywords from headline
            headline_words = [w.strip() for w in headline.replace(',', ' ').replace('|', ' ').split() if len(w) > 3]
            for word in headline_words[:3]:
                if word not in strengths:
                    strengths.append(word)
        
        # Determine learning style based on profession
        learning_style = self._infer_learning_style(headline, current_role.get('title', ''))
        
        # Generate career-aligned goals
        goals = self._generate_learning_goals(current_role, skills)
        
        # Generate recommended topics
        recommended_topics = self._generate_topic_recommendations(skills, current_role, headline)
        
        return {
            "success": True,
            "profile_data": {
                "full_name": raw_data.get('full_name', ''),
                "headline": headline,
                "summary": raw_data.get('summary', ''),
                "location": raw_data.get('city', '') + ', ' + raw_data.get('country_full_name', ''),
                "current_company": current_role.get('company', ''),
                "current_role": current_role.get('title', ''),
                "industry": raw_data.get('industry', ''),
                "connections": raw_data.get('connections', 0),
                "skills": skills,
                "experience_years": len(experiences),
                "education_level": highest_education.get('degree_name', ''),
                "school": highest_education.get('school', '')
            },
            "learner_profile": {
                "strengths": strengths[:5],
                "weaknesses": self._identify_skill_gaps(skills, current_role.get('title', '')),
                "goals": goals,
                "learning_style": learning_style,
                "recommended_topics": recommended_topics,
                "career_insights": self._generate_career_insights(current_role, skills),
                "profile_summary": f"{raw_data.get('full_name', 'Professional')} is a {current_role.get('title', 'professional')} with expertise in {', '.join(skills[:3]) if skills else 'their field'}."
            }
        }
    
    def _infer_learning_style(self, headline: str, title: str) -> str:
        """Infer learning style based on profession"""
        text = (headline + ' ' + title).lower()
        
        if any(word in text for word in ['designer', 'artist', 'creative', 'ui', 'ux', 'graphic']):
            return 'visual'
        elif any(word in text for word in ['developer', 'engineer', 'programmer', 'analyst', 'data']):
            return 'kinesthetic'
        elif any(word in text for word in ['manager', 'director', 'executive', 'consultant', 'coach']):
            return 'auditory'
        elif any(word in text for word in ['writer', 'editor', 'researcher', 'journalist', 'content']):
            return 'reading'
        else:
            return 'visual'
    
    def _identify_skill_gaps(self, skills: list, title: str) -> list:
        """Identify potential skill gaps based on role"""
        common_gaps = {
            'developer': ['leadership', 'communication', 'business strategy'],
            'engineer': ['project management', 'public speaking', 'marketing'],
            'manager': ['technical skills', 'data analysis', 'coding'],
            'designer': ['business acumen', 'data analysis', 'backend development'],
            'analyst': ['presentation skills', 'leadership', 'creative thinking'],
            'marketing': ['technical skills', 'data engineering', 'programming'],
            'sales': ['technical knowledge', 'data analysis', 'product development']
        }
        
        title_lower = title.lower()
        for role_key, gaps in common_gaps.items():
            if role_key in title_lower:
                return gaps[:3]
        
        return ['Advanced specialization', 'Cross-functional skills', 'Industry certifications']
    
    def _generate_learning_goals(self, current_role: dict, skills: list) -> list:
        """Generate career-aligned learning goals"""
        goals = []
        title = current_role.get('title', '').lower()
        
        if 'senior' in title or 'lead' in title:
            goals.append('Develop executive leadership skills')
            goals.append('Master strategic planning and decision-making')
        elif 'junior' in title or 'associate' in title:
            goals.append('Build technical expertise in core area')
            goals.append('Develop project management fundamentals')
        else:
            goals.append('Advance to senior/leadership position')
            goals.append('Expand cross-functional knowledge')
        
        goals.append('Stay current with industry trends and technologies')
        goals.append('Build professional network and personal brand')
        
        return goals[:5]
    
    def _generate_topic_recommendations(self, skills: list, current_role: dict, headline: str) -> list:
        """Generate personalized topic recommendations"""
        recommendations = []
        
        # Role-based recommendations
        title = current_role.get('title', '').lower()
        
        if 'developer' in title or 'engineer' in title:
            recommendations.extend(['System Design', 'Cloud Architecture', 'DevOps'])
        elif 'manager' in title or 'director' in title:
            recommendations.extend(['Leadership Excellence', 'Strategic Management', 'Team Building'])
        elif 'designer' in title:
            recommendations.extend(['UX Research', 'Design Systems', 'Product Strategy'])
        elif 'data' in title or 'analyst' in title:
            recommendations.extend(['Machine Learning', 'Data Visualization', 'Business Intelligence'])
        elif 'marketing' in title:
            recommendations.extend(['Digital Marketing', 'Analytics', 'Content Strategy'])
        else:
            recommendations.extend(['Professional Development', 'Industry Trends', 'Soft Skills'])
        
        # Add skill-based recommendations
        if 'python' in str(skills).lower():
            recommendations.append('Advanced Python')
        if 'leadership' in str(skills).lower():
            recommendations.append('Executive Coaching')
        
        return list(set(recommendations))[:5]
    
    def _generate_career_insights(self, current_role: dict, skills: list) -> str:
        """Generate personalized career insights"""
        title = current_role.get('title', 'Professional')
        company = current_role.get('company', 'their organization')
        
        insights = f"As a {title}, focus on deepening expertise while building leadership capabilities. "
        insights += "Consider expanding into adjacent areas to increase career versatility. "
        insights += "Continuous learning in emerging technologies will be valuable for long-term growth."
        
        return insights
    
    async def _ai_fallback_analysis(self, linkedin_url: str) -> Dict[str, Any]:
        """Fallback to AI-based profile analysis when API is unavailable"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            api_key = os.environ.get('EMERGENT_LLM_KEY')
            if not api_key:
                return {
                    "success": False,
                    "error": "LinkedIn analysis service not available"
                }
            
            system_message = """You are a career advisor analyzing a LinkedIn profile URL.
            Based on the URL structure and any information you can infer, generate a professional learner profile.
            Return a JSON object with:
            {
                "strengths": ["skill1", "skill2", "skill3"],
                "weaknesses": ["area1", "area2"],
                "goals": ["goal1", "goal2", "goal3"],
                "learning_style": "visual|auditory|kinesthetic|reading",
                "recommended_topics": ["topic1", "topic2", "topic3"],
                "career_insights": "Brief career advice",
                "profile_summary": "Professional summary"
            }"""
            
            import uuid
            chat = LlmChat(
                api_key=api_key,
                session_id=f"linkedin-{uuid.uuid4()}",
                system_message=system_message
            )
            chat.with_model("openai", "gpt-5.2")
            
            response = await chat.send_message(UserMessage(
                text=f"Analyze this LinkedIn profile and generate a learner profile: {linkedin_url}"
            ))
            
            # Try to parse JSON from response
            import json
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    profile_data = json.loads(response[json_start:json_end])
                else:
                    raise ValueError("No JSON found")
            except:
                profile_data = {
                    "strengths": ["Adaptability", "Communication", "Problem Solving"],
                    "weaknesses": ["Technical depth", "Industry expertise"],
                    "goals": ["Career advancement", "Skill development", "Leadership growth"],
                    "learning_style": "visual",
                    "recommended_topics": ["Professional Development", "Industry Trends", "Leadership"],
                    "career_insights": "Focus on continuous learning and building expertise in your field.",
                    "profile_summary": "Professional seeking to advance their career through continuous learning."
                }
            
            return {
                "success": True,
                "source": "ai_inference",
                "learner_profile": profile_data
            }
            
        except Exception as e:
            logger.error(f"AI fallback analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
linkedin_scraper = LinkedInScraperService()
