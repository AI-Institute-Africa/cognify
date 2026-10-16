"""
Social Media Profile Scraping Service using Proxycurl API
Extracts professional data for AI learning personalization
Supports both individual LinkedIn profiles and company pages
"""
import os
import re
import logging
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

PROXYCURL_API_KEY = os.environ.get('PROXYCURL_API_KEY', '')


class LinkedInScraperService:
    """Social Profile Scraper using Proxycurl API - supports individuals and companies"""
    
    def __init__(self):
        self.api_key = PROXYCURL_API_KEY
        self.base_url = "https://nubela.co/proxycurl/api/v2"
    
    def _detect_url_type(self, url: str) -> str:
        """Detect whether URL is a LinkedIn profile, company page, or other social media"""
        url_lower = url.lower().strip()
        if 'linkedin.com/company/' in url_lower or 'linkedin.com/school/' in url_lower:
            return 'linkedin_company'
        elif 'linkedin.com/in/' in url_lower:
            return 'linkedin_individual'
        elif 'linkedin.com' in url_lower:
            return 'linkedin_individual'
        elif 'github.com' in url_lower:
            return 'github'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        else:
            return 'unknown'
    
    async def analyze_url(self, url: str) -> Dict[str, Any]:
        """Analyze any social media URL - routes to appropriate scraper"""
        url_type = self._detect_url_type(url)
        
        if url_type == 'linkedin_company':
            return await self.scrape_company(url)
        elif url_type == 'linkedin_individual':
            return await self.scrape_profile(url)
        else:
            return await self._ai_social_analysis(url, url_type)
    
    async def scrape_profile(self, linkedin_url: str) -> Dict[str, Any]:
        """Scrape a LinkedIn profile and extract professional data"""
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
                    logger.error(f"Proxycurl API error: {response.status_code} - {response.text}")
                    return await self._ai_fallback_analysis(linkedin_url)
                    
        except Exception as e:
            logger.error(f"LinkedIn scraping error: {e}")
            return await self._ai_fallback_analysis(linkedin_url)
    
    async def scrape_company(self, company_url: str) -> Dict[str, Any]:
        """Scrape a LinkedIn company page and extract organizational data"""
        if not self.api_key:
            logger.warning("Proxycurl API key not configured, using AI inference fallback")
            return await self._ai_company_fallback(company_url)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/linkedin/company",
                    params={"url": company_url},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._transform_company_data(data)
                elif response.status_code == 404:
                    return {"success": False, "error": "Company page not found"}
                elif response.status_code == 401:
                    logger.error("Proxycurl API key invalid")
                    return await self._ai_company_fallback(company_url)
                else:
                    logger.error(f"Proxycurl company API error: {response.status_code} - {response.text}")
                    return await self._ai_company_fallback(company_url)
                    
        except Exception as e:
            logger.error(f"Company scraping error: {e}")
            return await self._ai_company_fallback(company_url)
    
    def _transform_profile_data(self, raw_data: Dict) -> Dict[str, Any]:
        """Transform raw Proxycurl data into learner profile format"""
        skills = []
        if raw_data.get('skills'):
            skills = [s for s in raw_data['skills'][:10]]
        
        experiences = raw_data.get('experiences', [])
        current_role = experiences[0] if experiences else {}
        
        education = raw_data.get('education', [])
        highest_education = education[0] if education else {}
        
        headline = raw_data.get('headline', '')
        strengths = skills[:5] if skills else []
        if headline and len(strengths) < 5:
            headline_words = [w.strip() for w in headline.replace(',', ' ').replace('|', ' ').split() if len(w) > 3]
            for word in headline_words[:3]:
                if word not in strengths:
                    strengths.append(word)
        
        learning_style = self._infer_learning_style(headline, current_role.get('title', ''))
        goals = self._generate_learning_goals(current_role, skills)
        recommended_topics = self._generate_topic_recommendations(skills, current_role, headline)
        
        return {
            "success": True,
            "url_type": "individual",
            "profile_data": {
                "full_name": raw_data.get('full_name', ''),
                "headline": headline,
                "summary": raw_data.get('summary', ''),
                "location": f"{raw_data.get('city', '')}, {raw_data.get('country_full_name', '')}".strip(', '),
                "current_company": current_role.get('company', ''),
                "current_role": current_role.get('title', ''),
                "industry": raw_data.get('industry', ''),
                "connections": raw_data.get('connections', 0),
                "skills": skills,
                "experience_years": len(experiences),
                "education_level": highest_education.get('degree_name', ''),
                "school": highest_education.get('school', ''),
                "profile_pic_url": raw_data.get('profile_pic_url', ''),
                "experiences": [
                    {
                        "title": exp.get('title', ''),
                        "company": exp.get('company', ''),
                        "starts_at": exp.get('starts_at'),
                        "ends_at": exp.get('ends_at'),
                        "description": exp.get('description', '')
                    }
                    for exp in experiences[:5]
                ],
                "education": [
                    {
                        "school": edu.get('school', ''),
                        "degree_name": edu.get('degree_name', ''),
                        "field_of_study": edu.get('field_of_study', ''),
                        "starts_at": edu.get('starts_at'),
                        "ends_at": edu.get('ends_at')
                    }
                    for edu in education[:5]
                ],
                "certifications": [
                    {
                        "name": cert.get('name', ''),
                        "authority": cert.get('authority', '')
                    }
                    for cert in raw_data.get('certifications', [])[:5]
                ],
                "languages": raw_data.get('languages', []),
                "volunteer_work": [
                    {
                        "title": vol.get('title', ''),
                        "company": vol.get('company', '')
                    }
                    for vol in raw_data.get('volunteer_work', [])[:3]
                ]
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
    
    def _transform_company_data(self, raw_data: Dict) -> Dict[str, Any]:
        """Transform raw Proxycurl company data into structured format"""
        specialities = raw_data.get('specialities', []) or []
        similar_companies = raw_data.get('similar_companies', []) or []
        
        return {
            "success": True,
            "url_type": "company",
            "company_data": {
                "name": raw_data.get('name', ''),
                "description": raw_data.get('description', ''),
                "tagline": raw_data.get('tagline', ''),
                "website": raw_data.get('website', ''),
                "industry": raw_data.get('industry', ''),
                "company_size": raw_data.get('company_size_on_linkedin', 0),
                "company_size_range": f"{raw_data.get('company_size', [None, None])}",
                "headquarters": raw_data.get('hq', {}).get('city', '') + ', ' + raw_data.get('hq', {}).get('country', '') if raw_data.get('hq') else '',
                "founded_year": raw_data.get('founded_year'),
                "company_type": raw_data.get('company_type', ''),
                "specialities": specialities[:10],
                "follower_count": raw_data.get('follower_count', 0),
                "logo_url": raw_data.get('profile_pic_url', ''),
                "cover_image_url": raw_data.get('background_cover_image_url', ''),
                "locations": [
                    {
                        "city": loc.get('city', ''),
                        "country": loc.get('country', ''),
                        "is_hq": loc.get('is_hq', False)
                    }
                    for loc in raw_data.get('locations', [])[:5]
                ],
                "similar_companies": [
                    {
                        "name": comp.get('name', ''),
                        "link": comp.get('link', ''),
                        "industry": comp.get('industry', '')
                    }
                    for comp in similar_companies[:5]
                ],
                "updates": raw_data.get('updates', [])[:3]
            },
            "insights": {
                "industry": raw_data.get('industry', 'Unknown'),
                "key_areas": specialities[:5],
                "recommended_courses": self._company_to_courses(raw_data),
                "company_summary": f"{raw_data.get('name', 'Company')} is a {raw_data.get('industry', 'technology')} company{' founded in ' + str(raw_data.get('founded_year')) if raw_data.get('founded_year') else ''}."
            }
        }
    
    def _company_to_courses(self, company_data: Dict) -> list:
        """Recommend courses based on company's industry and specialities"""
        recommendations = []
        industry = (company_data.get('industry') or '').lower()
        specialities = [s.lower() for s in (company_data.get('specialities') or [])]
        
        if any(kw in industry for kw in ['technology', 'software', 'internet']):
            recommendations.extend(['Software Engineering', 'Cloud Computing', 'Data Science'])
        elif any(kw in industry for kw in ['finance', 'banking', 'insurance']):
            recommendations.extend(['Financial Analysis', 'Risk Management', 'FinTech'])
        elif any(kw in industry for kw in ['health', 'medical', 'pharma']):
            recommendations.extend(['Healthcare Management', 'Medical Research', 'Biotech'])
        elif any(kw in industry for kw in ['education', 'e-learning']):
            recommendations.extend(['EdTech', 'Curriculum Design', 'Learning Analytics'])
        else:
            recommendations.extend(['Business Strategy', 'Digital Transformation', 'Leadership'])
        
        for spec in specialities[:3]:
            if spec not in recommendations:
                recommendations.append(spec.title())
        
        return recommendations[:6]
    
    def _infer_learning_style(self, headline: str, title: str) -> str:
        text = (headline + ' ' + title).lower()
        if any(word in text for word in ['designer', 'artist', 'creative', 'ui', 'ux', 'graphic']):
            return 'visual'
        elif any(word in text for word in ['developer', 'engineer', 'programmer', 'analyst', 'data']):
            return 'kinesthetic'
        elif any(word in text for word in ['manager', 'director', 'executive', 'consultant', 'coach']):
            return 'auditory'
        elif any(word in text for word in ['writer', 'editor', 'researcher', 'journalist', 'content']):
            return 'reading'
        return 'visual'
    
    def _identify_skill_gaps(self, skills: list, title: str) -> list:
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
        recommendations = []
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
        if 'python' in str(skills).lower():
            recommendations.append('Advanced Python')
        if 'leadership' in str(skills).lower():
            recommendations.append('Executive Coaching')
        return list(set(recommendations))[:5]
    
    def _generate_career_insights(self, current_role: dict, skills: list) -> str:
        title = current_role.get('title', 'Professional')
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
                return {"success": False, "error": "LinkedIn analysis service not available"}
            
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
            
            import uuid as uuid_mod
            chat = LlmChat(
                api_key=api_key,
                session_id=f"linkedin-{uuid_mod.uuid4()}",
                system_message=system_message
            )
            chat.with_model("openai", "gpt-5.2")
            
            response = await chat.send_message(UserMessage(
                text=f"Analyze this LinkedIn profile and generate a learner profile: {linkedin_url}"
            ))
            
            import json
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    profile_data = json.loads(response[json_start:json_end])
                else:
                    raise ValueError("No JSON found")
            except Exception:
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
                "url_type": "individual",
                "source": "ai_inference",
                "learner_profile": profile_data
            }
            
        except Exception as e:
            logger.error(f"AI fallback analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _ai_company_fallback(self, company_url: str) -> Dict[str, Any]:
        """Fallback to AI-based company analysis when Proxycurl is unavailable"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            api_key = os.environ.get('EMERGENT_LLM_KEY')
            if not api_key:
                return {"success": False, "error": "Company analysis service not available"}
            
            import uuid as uuid_mod
            chat = LlmChat(
                api_key=api_key,
                session_id=f"company-{uuid_mod.uuid4()}",
                system_message="""You are a business analyst. Analyze the given company URL and provide information.
                Return a JSON object with:
                {
                    "name": "Company name",
                    "industry": "Industry",
                    "description": "Brief description",
                    "key_areas": ["area1", "area2"],
                    "recommended_courses": ["course1", "course2"],
                    "company_summary": "Summary"
                }"""
            )
            chat.with_model("openai", "gpt-5.2")
            
            response = await chat.send_message(UserMessage(
                text=f"Analyze this company URL and provide company information: {company_url}"
            ))
            
            import json
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    company_data = json.loads(response[json_start:json_end])
                else:
                    raise ValueError("No JSON found")
            except Exception:
                company_data = {
                    "name": "Unknown Company",
                    "industry": "Technology",
                    "description": "Company information unavailable",
                    "key_areas": ["Innovation", "Technology"],
                    "recommended_courses": ["Business Strategy", "Digital Transformation"],
                    "company_summary": "Company analysis pending."
                }
            
            return {
                "success": True,
                "url_type": "company",
                "source": "ai_inference",
                "company_data": company_data,
                "insights": company_data
            }
            
        except Exception as e:
            logger.error(f"AI company fallback error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _ai_social_analysis(self, url: str, url_type: str) -> Dict[str, Any]:
        """AI-based analysis for non-LinkedIn social media URLs"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            api_key = os.environ.get('EMERGENT_LLM_KEY')
            if not api_key:
                return {"success": False, "error": "Social media analysis service not available"}
            
            import uuid as uuid_mod
            chat = LlmChat(
                api_key=api_key,
                session_id=f"social-{uuid_mod.uuid4()}",
                system_message="""You are a professional profile analyst. Analyze the given social media URL
                and infer what you can about the person or organization.
                Return a JSON object with:
                {
                    "name": "Name if identifiable",
                    "type": "individual or company",
                    "platform": "github/twitter/other",
                    "inferred_skills": ["skill1", "skill2"],
                    "inferred_interests": ["interest1", "interest2"],
                    "recommended_topics": ["topic1", "topic2"],
                    "profile_summary": "Brief summary",
                    "career_insights": "Career advice based on profile"
                }"""
            )
            chat.with_model("openai", "gpt-5.2")
            
            response = await chat.send_message(UserMessage(
                text=f"Analyze this {url_type} social media profile URL: {url}"
            ))
            
            import json
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    data = json.loads(response[json_start:json_end])
                else:
                    raise ValueError("No JSON found")
            except Exception:
                data = {
                    "name": "Unknown",
                    "type": "unknown",
                    "platform": url_type,
                    "inferred_skills": [],
                    "inferred_interests": [],
                    "recommended_topics": ["Professional Development"],
                    "profile_summary": "Unable to analyze this profile.",
                    "career_insights": "Consider linking a LinkedIn profile for better analysis."
                }
            
            return {
                "success": True,
                "url_type": url_type,
                "source": "ai_inference",
                "social_data": data,
                "learner_profile": {
                    "strengths": data.get('inferred_skills', [])[:5],
                    "weaknesses": [],
                    "goals": [],
                    "learning_style": "visual",
                    "recommended_topics": data.get('recommended_topics', []),
                    "career_insights": data.get('career_insights', ''),
                    "profile_summary": data.get('profile_summary', '')
                }
            }
            
        except Exception as e:
            logger.error(f"Social media analysis error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
linkedin_scraper = LinkedInScraperService()
